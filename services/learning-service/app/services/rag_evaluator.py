"""Golden-dataset RAG benchmark: three conditions answer the same 40 questions, and every number is measured.

  baseline   the LLM answers from its own knowledge (no retrieval)
  naive      dense vector search only, top 3 chunks
  advanced   the production pipeline: hybrid search (dense + keyword, RRF), cross-encoder re-ranking and
             compression, top 4 chunks (learning_rag.retrieve_context)

All three answer with the same prompt, so only the retrieval differs. Per answer:
  context_precision  1 / rank of the first chunk from the question's ground-truth document (0 if absent)
  context_recall     share of the question's ground-truth keywords present in the retrieved context
  faithfulness       LLM judge: share of the answer's factual claims supported by the retrieved context
                     (none for the baseline, which has no context to be faithful to)
  answer_relevance   LLM judge: how fully the answer addresses the question, 1-5 scaled to 0-1
  latency_ms, prompt_tokens (characters / 4)
Significance: paired sign-flip permutation test on per-question faithfulness, advanced vs naive.
The judge is the same local LLM that writes the answers (a known bias of LLM-as-judge; see method_notes).
"""
import asyncio
import json
import os
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import RagBenchmarkRun
from app.schemas.learning import BenchmarkRunStatus, ComparativeBenchmarkMatrixResponse, RAGTriadMetrics
from app.services.learning_rag import LLMUnavailable, learning_rag_service
from app.services.vector_store import vector_store_service

STRATEGIES = {
    "baseline": "Baseline (Direct LLM / No Retrieval)",
    "naive_rag": "Naive RAG (Dense Vector Search Only)",
    "advanced_rag": "Advanced RAG (Hybrid RRF + Re-Ranker + Compression)",
}
PERMUTATIONS = 10_000
STALE_RUN = timedelta(hours=3)       # a "running" run older than this died with its process
METHOD_NOTES = (
    "Same answer prompt for all three conditions; only retrieval differs. Precision: 1/rank of the ground-truth "
    "document in the retrieved chunks. Recall: share of ground-truth keywords in the retrieved context. "
    "Faithfulness and relevance are judged by the same local LLM that writes the answers (LLM-as-judge, which "
    "can favour its own outputs). p-value: paired sign-flip permutation test, advanced vs naive faithfulness."
)


def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


def context_precision(titles: List[str], ground_truth_title: str) -> float:
    """1 / rank of the first retrieved chunk from the ground-truth document; 0 if none was retrieved."""
    target = ground_truth_title.lower().strip()
    for rank, title in enumerate(titles, 1):
        t = (title or "").lower().strip()
        if t and (t == target or target in t or t in target):
            return round(1.0 / rank, 4)
    return 0.0


def context_recall(context: str, keywords: List[str]) -> Optional[float]:
    """Share of the ground-truth keywords that appear in the retrieved context."""
    if not keywords:
        return None
    ctx = context.lower()
    return round(sum(1 for k in keywords if k.lower() in ctx) / len(keywords), 4)


def permutation_p_value(diffs: List[float], n: int = PERMUTATIONS, seed: int = 7) -> Optional[float]:
    """Two-sided paired sign-flip permutation test of mean(diffs) = 0."""
    if len(diffs) < 3:
        return None
    observed = abs(sum(diffs) / len(diffs))
    rng = random.Random(seed)
    extreme = 0
    for _ in range(n):
        if abs(sum(d if rng.random() < 0.5 else -d for d in diffs) / len(diffs)) >= observed - 1e-12:
            extreme += 1
    return round((extreme + 1) / (n + 1), 4)


def _mean(values: List[Optional[float]]) -> Optional[float]:
    v = [x for x in values if x is not None]
    return round(sum(v) / len(v), 4) if v else None


class RAGEvaluatorService:
    def __init__(self):
        self._dataset_cache: Optional[List[Dict[str, Any]]] = None
        self._tasks: set = set()          # running benchmark tasks (asyncio keeps only weak references)

    def load_golden_dataset(self) -> List[Dict[str, Any]]:
        if self._dataset_cache is None:
            path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "evaluation", "golden_dataset.json")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Golden dataset not found at: {path}")
            with open(path, "r", encoding="utf-8") as f:
                self._dataset_cache = json.load(f)
        return self._dataset_cache

    # ------------------------------------------------------------ one question, three conditions
    async def _answer(self, question: str, role: str, context: Optional[str]) -> Dict[str, Any]:
        system = (f"You are a learning assistant for a student preparing for a {role} career. "
                  "Answer the question clearly and accurately in under 200 words.")
        if context is not None:
            system += f"\nUse only the context below and say if it doesn't cover the question.\n\nCONTEXT:\n{context}"
        t0 = time.perf_counter()
        text = ""
        async for piece in learning_rag_service.stream_text(system, f"Question: {question}", max_tokens=400,
                                                            temperature=0.0):
            text += piece
        return {"answer": text.strip(), "generation_ms": round((time.perf_counter() - t0) * 1000, 1),
                "prompt_tokens": _tokens(system + question)}

    async def _judge(self, question: str, answer: str, context: Optional[str]) -> Dict[str, Optional[float]]:
        """LLM-as-judge: claims supported by the context, and relevance to the question."""
        if not answer:
            return {"faithfulness": None, "answer_relevance": None}
        task = ("Rate how fully the ANSWER addresses the QUESTION: relevance 1 (off-topic) to 5 (complete).\n")
        if context is not None:
            task += ("List the ANSWER's factual claims and count how many are directly supported by the CONTEXT.\n")
        system = ("You are a strict evaluator of a retrieval-augmented answer.\n" + task +
                  "Return JSON: {\"relevance\": integer 1-5"
                  + (", \"claims_total\": integer, \"claims_supported\": integer" if context is not None else "")
                  + "}.")
        user = (f"QUESTION: {question}\n\nANSWER: {answer}"
                + (f"\n\nCONTEXT:\n{context}" if context is not None else ""))
        try:
            data = await learning_rag_service.generate_json(system, user, max_tokens=300, temperature=0.0)
        except LLMUnavailable:
            return {"faithfulness": None, "answer_relevance": None}
        relevance = None
        try:
            relevance = round((min(5, max(1, int(data.get("relevance")))) - 1) / 4, 4)
        except (TypeError, ValueError):
            pass
        faithfulness = None
        if context is not None:
            try:
                total, supported = int(data.get("claims_total")), int(data.get("claims_supported"))
                if total > 0:
                    faithfulness = round(min(supported, total) / total, 4)
            except (TypeError, ValueError):
                pass
        return {"faithfulness": faithfulness, "answer_relevance": relevance}

    async def evaluate_single_item(self, session: AsyncSession, item: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the three conditions on one golden question and measures each answer."""
        query, role = item["query"], item["target_role"]
        gt_title, keywords = item["ground_truth_doc_title"], item["ground_truth_keywords"]
        out: Dict[str, Any] = {"id": item["id"], "query": query}

        # Baseline: no retrieval
        gen = await self._answer(query, role, None)
        out["baseline"] = {**await self._judge(query, gen["answer"], None), "context_precision": None,
                           "context_recall": None, "latency_ms": gen["generation_ms"],
                           "tokens": gen["prompt_tokens"], "answer": gen["answer"]}

        # Naive RAG: dense search only, top 3
        t0 = time.perf_counter()
        chunks = await vector_store_service.search_dense_chunks(session, query, role, limit=3)
        retrieval_ms = (time.perf_counter() - t0) * 1000
        context = "\n\n".join(f"[Source {i}: {c['title']}]\n{c['content']}" for i, c in enumerate(chunks, 1))
        gen = await self._answer(query, role, context)
        out["naive_rag"] = {**await self._judge(query, gen["answer"], context),
                            "context_precision": context_precision([c["title"] for c in chunks], gt_title),
                            "context_recall": context_recall(context, keywords),
                            "latency_ms": round(retrieval_ms + gen["generation_ms"], 1),
                            "tokens": gen["prompt_tokens"], "answer": gen["answer"],
                            "retrieved_titles": [c["title"] for c in chunks]}

        # Advanced RAG: the production retrieval (hybrid + re-ranker + compression)
        t0 = time.perf_counter()
        ctx = await learning_rag_service.retrieve_context(session, query, role)
        retrieval_ms = (time.perf_counter() - t0) * 1000
        gen = await self._answer(query, role, ctx["context"])
        titles = [c["title"] for c in ctx["items"]]
        out["advanced_rag"] = {**await self._judge(query, gen["answer"], ctx["context"]),
                               "context_precision": context_precision(titles, gt_title),
                               "context_recall": context_recall(ctx["context"], keywords),
                               "latency_ms": round(retrieval_ms + gen["generation_ms"], 1),
                               "tokens": gen["prompt_tokens"], "answer": gen["answer"],
                               "retrieved_titles": titles,
                               "compression_saved_percent": ctx.get("tokens_saved_percent")}
        return out

    # ------------------------------------------------------------ full benchmark runs
    @staticmethod
    def summarise(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        summary = {}
        for key in STRATEGIES:
            r = [row[key] for row in rows if key in row]
            summary[key] = {m: _mean([x.get(m) for x in r]) for m in
                            ("faithfulness", "answer_relevance", "context_precision", "context_recall",
                             "latency_ms", "tokens")}
        diffs = [row["advanced_rag"]["faithfulness"] - row["naive_rag"]["faithfulness"] for row in rows
                 if row["advanced_rag"].get("faithfulness") is not None
                 and row["naive_rag"].get("faithfulness") is not None]
        return {"summary": summary, "faithfulness_pairs": len(diffs), "p_value": permutation_p_value(diffs),
                "compression_saved_percent": _mean([row["advanced_rag"].get("compression_saved_percent")
                                                    for row in rows])}

    async def start_run(self, session: AsyncSession) -> BenchmarkRunStatus:
        """Starts a full run in the background (about a minute per question with the local LLM), unless one
        is already running."""
        now = datetime.now(timezone.utc)
        running = (await session.execute(select(RagBenchmarkRun).where(RagBenchmarkRun.status == "running"))
                   ).scalars().all()
        for run in running:
            if run.started_at and now - run.started_at > STALE_RUN:
                run.status, run.error, run.finished_at = "failed", "Interrupted (service restarted)", now
            else:
                return self._status(run)
        run = RagBenchmarkRun(status="running", items_total=len(self.load_golden_dataset()), items_done=0)
        session.add(run)
        await session.commit()
        task = asyncio.create_task(self._run(run.id))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return self._status(run)

    async def _run(self, run_id: uuid.UUID):
        from app.core.database import AsyncSessionLocal
        rows: List[Dict[str, Any]] = []
        async with AsyncSessionLocal() as session:
            run = await session.get(RagBenchmarkRun, run_id)
            try:
                for item in self.load_golden_dataset():
                    rows.append(await self.evaluate_single_item(session, item))
                    run.items_done = len(rows)
                    run.results = {"rows": rows}
                    await session.commit()
                run.results = {**self.summarise(rows), "rows": rows}
                run.status = "done"
            except Exception as e:
                run.status, run.error = "failed", f"{type(e).__name__}: {e}"[:2000]
                print(f"[Warning] RAG benchmark run failed: {e}")
            run.finished_at = datetime.now(timezone.utc)
            await session.commit()

    @staticmethod
    def _status(run: Optional[RagBenchmarkRun]) -> BenchmarkRunStatus:
        if run is None:
            return BenchmarkRunStatus(status="none")
        return BenchmarkRunStatus(run_id=str(run.id), status=run.status, items_done=run.items_done or 0,
                                  items_total=run.items_total or 0,
                                  started_at=run.started_at.isoformat() if run.started_at else None,
                                  finished_at=run.finished_at.isoformat() if run.finished_at else None,
                                  error=run.error)

    async def latest_status(self, session: AsyncSession) -> BenchmarkRunStatus:
        run = (await session.execute(select(RagBenchmarkRun).order_by(RagBenchmarkRun.started_at.desc()).limit(1))
               ).scalar_one_or_none()
        return self._status(run)

    async def latest_matrix(self, session: AsyncSession) -> Optional[ComparativeBenchmarkMatrixResponse]:
        """The most recent completed run, or None if the benchmark hasn't been run yet."""
        run = (await session.execute(select(RagBenchmarkRun).where(RagBenchmarkRun.status == "done")
                                     .order_by(RagBenchmarkRun.finished_at.desc()).limit(1))).scalar_one_or_none()
        if not run or not run.results or "summary" not in run.results:
            return None
        res = run.results
        s = res["summary"]

        def metrics(key: str) -> RAGTriadMetrics:
            m = s[key]
            return RAGTriadMetrics(strategy_name=STRATEGIES[key], faithfulness=m["faithfulness"],
                                   answer_relevance=m["answer_relevance"] or 0.0,
                                   context_precision=m["context_precision"] or 0.0,
                                   context_recall=m["context_recall"] or 0.0,
                                   average_latency_ms=m["latency_ms"] or 0.0, prompt_tokens=int(m["tokens"] or 0))

        adv, naive = s["advanced_rag"], s["naive_rag"]
        parts = []
        for label, metric in (("faithfulness", "faithfulness"), ("context precision", "context_precision"),
                              ("context recall", "context_recall"), ("answer relevance", "answer_relevance")):
            if adv[metric] is not None and naive[metric] is not None:
                parts.append(f"{label} {adv[metric] * 100:.1f}% vs {naive[metric] * 100:.1f}%")
        p = res.get("p_value")
        conclusion = (f"Advanced RAG vs naive dense retrieval on {len(res['rows'])} golden questions: "
                      + "; ".join(parts) + ". "
                      + (f"Faithfulness difference: p = {p} (paired permutation test, "
                         f"{res['faithfulness_pairs']} questions)." if p is not None else
                         "Too few judged answers for a significance test."))
        return ComparativeBenchmarkMatrixResponse(
            sample_size=len(res["rows"]), baseline_direct_llm=metrics("baseline"), naive_rag_dense=metrics("naive_rag"),
            advanced_rag_hybrid_rerank=metrics("advanced_rag"), p_value_statistical_significance=p,
            research_conclusion=conclusion, run_id=str(run.id),
            run_finished_at=run.finished_at.isoformat() if run.finished_at else None,
            compression_saved_percent=res.get("compression_saved_percent"), method_notes=METHOD_NOTES)


rag_evaluator_service = RAGEvaluatorService()
