"""Turns interview candidates into question-bank items with grounded reference answers and rubrics.

Runs inside the learning-service container (it needs the curriculum vector store and the local LLM);
scripts/datasets/build_interview_bank.sh copies it in and the results out.

    python generate_interview_bank.py CANDIDATES.jsonl GENERATED.jsonl     # resumable
    python generate_interview_bank.py --finalize GENERATED.jsonl BANK.json

For every candidate the LLM gets the question (or, for document candidates, a curriculum document to
write a question from), the source's own answer if it has one, and the closest curriculum passages.
It must answer only from that material and rejects questions that are trivia, opinion, or not
covered by it. Rejections are kept in GENERATED.jsonl with the reason, so the yield can be reported.
"""
import asyncio
import json
import os
import re
import sys
from collections import Counter

LEVELS = ["Entry Level", "Mid Level", "Senior Level"]

SYSTEM = """You build a technical interview question bank for {role} candidates. Use ONLY the source answer
and reference passages given; do not add facts they don't support.

Return a JSON object with keys:
- "keep": false if the question is trivia, a joke, asks for personal opinions or favourites, needs a
  whiteboard or code to answer, is not relevant to a {role}, or the material doesn't support a correct answer
- "reject_reason": short reason when keep is false, else ""
- "level": one of "Entry Level", "Mid Level", "Senior Level"{level_hint}
- "topic": 2-4 word topic, e.g. "Container Networking"
- "title": short title, at most 8 words
- "question": the question as an interviewer says it out loud, one or two sentences, answerable in 1-3 minutes of speech
- "expected_answer": 3-6 sentences a strong candidate would say, supported by the material
- "criteria": 3-4 concrete points a good answer covers
- "high_score_criteria": one sentence describing a 5/5 answer
- "low_score_criteria": one sentence describing a weak answer or common misconception"""


# Non-technical roles (HR, marketing, finance, writing, design, brand): competency-based interviews
SYSTEM_NON_TECHNICAL = """You build an interview question bank for {role} candidates. Use ONLY the competency, role
profile and reference passages given; do not add facts they don't support.

Return a JSON object with keys:
- "keep": false if the question would be trivia, ask for personal opinions or favourites, be illegal to ask in an
  interview (age, family, religion, health), not be relevant to a {role}, or the material doesn't support a good answer
- "reject_reason": short reason when keep is false, else ""
- "level": one of "Entry Level", "Mid Level", "Senior Level"{level_hint}
- "topic": 2-4 word topic, e.g. "Performance Reviews"
- "title": short title, at most 8 words
- "question": the question as an interviewer says it out loud, one or two sentences, answerable in 1-3 minutes of speech;
  behavioural ("Tell me about a time...") or situational ("How would you handle...") for competencies, or a knowledge
  question for documents
- "expected_answer": 3-6 sentences describing what a strong candidate would cover: the actions, considerations and
  results (and, for knowledge questions, the facts), supported by the material
- "criteria": 3-4 concrete points a good answer covers
- "high_score_criteria": one sentence describing a 5/5 answer (specific example, clear actions, measurable result)
- "low_score_criteria": one sentence describing a weak answer or common mistake"""


def passages_text(passages) -> str:
    return "\n\n".join(f"[{p['title']} ({p['source']})]\n{p['content'][:900]}" for p in passages)


async def retrieve(session, query: str, role: str, top_k: int = 3):
    from app.services.vector_store import vector_store_service
    results = await vector_store_service.search_learning_chunks(session=session, query=query, target_role=role, top_k=top_k)
    return [{"title": r["title"], "source": r["source"], "url": r.get("url"), "content": r["content"]} for r in results]


async def process(session, c: dict) -> dict:
    from app.services.local_llm import local_llm
    level_hint = f' (the source says {c["level"]}; keep it unless clearly wrong)' if c.get("level") else ""
    system = (SYSTEM if c.get("technical", True) else SYSTEM_NON_TECHNICAL).format(role=c["role"], level_hint=level_hint)
    if c["kind"] == "competency":
        system += (f'\nWrite ONE {c["level"]} behavioural or situational interview question assessing the competency '
                   f'below, as a {c["role"]} would apply it at work.')
        passages = await retrieve(session, c["competency"], c["role"], top_k=4)
        user = f"Competency (core task of the role, from O*NET): {c['competency']}\n"
        user += f"\nReference passages:\n{passages_text(passages) or 'none'}"
    elif c["kind"] == "design":
        # A full "design X" needs a whiteboard; ask about one part of the design instead
        system += ("\nThis is a system design problem. Do NOT ask the candidate to design the whole system. Write ONE "
                   "focused spoken question about a single part that the material explains (for example data storage, "
                   "caching, scaling reads or writes, ID generation, or a trade-off), answerable in 2-3 minutes without "
                   "a whiteboard. Mention the product for context. Reject only if the material explains no part of it.")
        passages = await retrieve(session, c["question"], c["role"], top_k=5)
        user = f"System design problem: {c['question']}\n"
        if c.get("source_answer"):
            user += f"\nWorked design ({c['source']}):\n{c['source_answer']}\n"
        user += f"\nReference passages:\n{passages_text(passages) or 'none'}"
    elif c["kind"] == "document":
        system += (f'\nWrite ONE {c["level"]} interview question that the document below answers well, '
                   f'about a concept a {c["role"]} must understand (not a product detail or a version number).')
        passages = []
        user = f"Document ({c['source']}):\n{c['document']}"
    else:
        passages = await retrieve(session, c["question"], c["role"])
        user = f"Question: {c['question']}\n"
        if c.get("source_answer"):
            user += f"\nSource answer ({c['source']}):\n{c['source_answer']}\n"
        user += f"\nReference passages:\n{passages_text(passages) or 'none'}"
    data = await local_llm.chat_json(system, user, temperature=0.2, max_tokens=900)
    return {"candidate": {k: c.get(k) for k in ("id", "kind", "role", "source", "license", "url")},
            "passages": [{k: p[k] for k in ("title", "source", "url")} for p in passages], "result": data}


async def generate(cand_path: str, out_path: str):
    from app.core.database import AsyncSessionLocal
    done = set()
    if os.path.exists(out_path):
        with open(out_path) as f:
            done = {json.loads(line)["candidate"]["id"] for line in f if line.strip()}
    with open(cand_path) as f:
        todo = [c for c in map(json.loads, f) if c["id"] not in done]
    print(f"{len(done)} done, {len(todo)} to go", flush=True)
    async with AsyncSessionLocal() as session:
        for i, c in enumerate(todo, 1):
            try:
                row = await process(session, c)
            except Exception as e:                      # keep going; failures are listed at the end
                row = {"candidate": {"id": c["id"], "kind": c["kind"], "role": c["role"], "source": c["source"]},
                       "error": str(e)[:300]}
            with open(out_path, "a") as f:
                f.write(json.dumps(row) + "\n")
            r = row.get("result", {})
            status = "ERROR" if "error" in row else ("kept" if r.get("keep") else f"rejected: {r.get('reject_reason', '')}")
            print(f"[{i}/{len(todo)}] {c['id']} {c['role']}: {(r.get('question') or c.get('question') or '')[:70]} -> {status}",
                  flush=True)


# The model sometimes refers to its inputs ("According to the provided information, ...")
LEAD_IN = re.compile(r"^(according to|based on|as described in|as per|from) (the |this )?(provided |given |above )?"
                     r"(information|text|passages?|documents?|documentation|material|source|context)[^,]*,\s*", re.I)
MATERIAL_REF = re.compile(r"\b(the|this) (provided |given |above )?(passage|passages|document|source answer|"
                          r"reference passages?|provided (text|information|material|context))\b", re.I)


def speakable(text) -> str:
    text = LEAD_IN.sub("", str(text or "").strip())
    return text[:1].upper() + text[1:]


def finalize(gen_path: str, bank_path: str, cand_path: str = None):
    """Valid kept items -> the interview-service question bank format. Where the candidate has a level
    (the source's own, e.g. Junior/Regular/Senior sysadmin, or the one a question was written at) it is
    kept: the LLM labelled almost everything "Mid Level"."""
    items, seen, stats = [], Counter(), Counter()
    levels = {}
    if cand_path:
        with open(cand_path) as f:
            levels = {c["id"]: c.get("level") for c in map(json.loads, f)}
    with open(gen_path) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    for row in rows:
        c, r = row["candidate"], row.get("result") or {}
        if "error" in row:
            stats["error"] += 1
            continue
        if not r.get("keep"):
            stats["rejected"] += 1
            continue
        criteria = [str(x).strip() for x in (r.get("criteria") or []) if str(x).strip()]
        question, answer = speakable(r.get("question")), speakable(r.get("expected_answer"))
        if MATERIAL_REF.search(question) or MATERIAL_REF.search(answer):
            stats["mentions_source"] += 1             # "the passage says..." can't be asked or answered aloud
            continue
        level = levels.get(c["id"]) or r.get("level")
        if level not in LEVELS or len(question) < 15 or len(answer) < 80 or len(criteria) < 2:
            stats["invalid"] += 1
            continue
        title = re.sub(r"\s+", " ", str(r.get("title") or question))[:120].strip()
        seen[(title, c["role"])] += 1
        if seen[(title, c["role"])] > 1:                # ingestion matches on (title, role)
            title = f"{title} ({seen[(title, c['role'])]})"
        grounded = sorted({p["source"] for p in row.get("passages", [])})
        source = (f"Generated from {c['source']} ({c['license']})" if c["kind"] == "document"
                  else f"{c['source']} ({c['license']})")
        items.append({
            "title": title, "role": c["role"], "topic": str(r.get("topic") or "General")[:100],
            "difficulty": level, "source": source[:255], "content": question, "expected_answer": answer,
            "rubric": {
                "criteria": criteria[:4],
                "high_score_criteria": str(r.get("high_score_criteria") or ""),
                "low_score_criteria": str(r.get("low_score_criteria") or ""),
            },
            "provenance": {"candidate_id": c["id"], "url": c.get("url"), "grounded_in": grounded},
        })
        stats["kept"] += 1
    with open(bank_path, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(dict(stats), f"-> {len(items)} items in {bank_path}")
    print(Counter((i["role"], i["difficulty"]) for i in items))


if __name__ == "__main__":
    if sys.argv[1] == "--finalize":
        finalize(*sys.argv[2:5])
    else:
        asyncio.run(generate(sys.argv[1], sys.argv[2]))
