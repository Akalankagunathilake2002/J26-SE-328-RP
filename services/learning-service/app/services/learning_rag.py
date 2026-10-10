import time
import json
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.services.vector_store import vector_store_service
from app.schemas.learning import (
    LearningQueryRequest,
    LearningQueryResponse,
    SourceCitation,
    RetrievedChunkDebug,
    BenchmarkComparisonResponse
)


class LearningRAGService:
    def __init__(self):
        self._llm = None
        self._init_llm()

    def _init_llm(self):
        if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            try:
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model=settings.LLM_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                    api_key=settings.OPENAI_API_KEY
                )
            except Exception as e:
                print(f"[Warning] Failed to initialize LangChain ChatOpenAI: {e}. Fallback to template generator.")
                self._llm = None
        elif settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self._llm = "gemini"
            except Exception as e:
                print(f"[Warning] Failed to initialize Google GenAI Client: {e}")
                self._gemini_client = None
                self._llm = None
        else:
            self._gemini_client = None
            self._llm = None

    async def execute_rag(self, session: AsyncSession, request: LearningQueryRequest) -> LearningQueryResponse:
        """
        Executes the full Personalized Learning RAG pipeline:
        Query -> pgvector Semantic Search -> Grounded Prompt Construction -> LLM -> Grounded Output
        """
        # Step 1: Retrieval
        t_retrieval_start = time.perf_counter()
        retrieved_results = await vector_store_service.search_learning_chunks(
            session=session,
            query=request.question,
            target_role=request.target_role,
            top_k=settings.TOP_K
        )
        retrieval_latency_ms = round((time.perf_counter() - t_retrieval_start) * 1000, 2)

        # Format debug chunks & citations
        debug_chunks: List[RetrievedChunkDebug] = []
        sources: List[SourceCitation] = []
        seen_sources = set()

        context_texts = []
        for i, item in enumerate(retrieved_results, 1):
            debug_chunks.append(RetrievedChunkDebug(
                chunk_id=item["chunk_id"],
                content_preview=item["content"][:200] + ("..." if len(item["content"]) > 200 else ""),
                similarity_score=item["similarity_score"],
                source=item["source"],
                topic=item["topic"],
                dense_rank=item.get("dense_rank"),
                sparse_rank=item.get("sparse_rank"),
                rrf_score=item.get("rrf_score"),
                retrieval_method=item.get("retrieval_method", "hybrid_rrf")
            ))

            src_key = (item["title"], item["source"])
            if src_key not in seen_sources:
                sources.append(SourceCitation(
                    title=item["title"],
                    source=item["source"],
                    url=item.get("url"),
                    topic=item.get("topic")
                ))
                seen_sources.add(src_key)

            context_texts.append(
                f"[Source {i}: {item['title']} ({item['source']})]\n{item['content']}"
            )

        formatted_context = "\n\n".join(context_texts) if context_texts else "No specific documents found."

        # Step 2: Grounded Prompt Construction & Generation
        t_gen_start = time.perf_counter()

        system_prompt = (
            f"You are the Personalized Learning Assistant for the Academic-to-Industry Skill Bridge Platform.\n"
            f"Student Profile:\n"
            f"- Target Career Role: {request.target_role}\n"
            f"- Current Skills: {', '.join(request.current_skills) if request.current_skills else 'Beginner'}\n"
            f"- Upstream Learning Priority: {request.learning_priority or 'General Curriculum'}\n\n"
            f"GROUNDING INSTRUCTIONS:\n"
            f"1. Explain the answer with direct relevance to the student's target role.\n"
            f"2. Ground your technical explanation strictly on the retrieved educational context below.\n"
            f"3. Cite source titles when explaining facts.\n"
            f"4. Propose a logical 'recommended_next_topic' advancing the student's industry readiness.\n"
            f"5. Return your response as a valid JSON object with keys: 'answer' (string) and 'recommended_next_topic' (string).\n\n"
            f"RETRIEVED EDUCATIONAL CONTEXT:\n{formatted_context}"
        )

        user_prompt = f"Student Question: {request.question}"

        answer_text, next_topic = await self._generate_response(system_prompt, user_prompt, retrieved_results)
        generation_latency_ms = round((time.perf_counter() - t_gen_start) * 1000, 2)
        total_latency_ms = round(retrieval_latency_ms + generation_latency_ms, 2)

        return LearningQueryResponse(
            answer=answer_text,
            recommended_next_topic=next_topic,
            sources=sources,
            retrieved_chunks=debug_chunks,
            retrieval_latency_ms=retrieval_latency_ms,
            generation_latency_ms=generation_latency_ms,
            total_latency_ms=total_latency_ms,
            retrieval_strategy=settings.RETRIEVAL_STRATEGY
        )

    async def execute_baseline(self, request: LearningQueryRequest) -> Dict[str, Any]:
        """
        Executes Baseline (Direct LLM prompting with no retrieval) for research ablation experiments.
        """
        t_start = time.perf_counter()
        prompt = (
            f"You are an AI assistant answering a student query.\n"
            f"Target Role: {request.target_role}\n"
            f"Question: {request.question}\n"
            f"Provide an ungrounded general technical response."
        )

        if self._llm == "gemini" and self._gemini_client:
            try:
                resp = self._gemini_client.models.generate_content(
                    model=settings.LLM_MODEL or "gemini-2.5-flash",
                    contents=prompt
                )
                baseline_text = resp.text.strip()
            except Exception as e:
                print(f"[Warning] Gemini baseline generation error: {e}")
                baseline_text = f"Baseline general response for {request.question} (LLM offline)."
        elif self._llm:
            try:
                from langchain_core.messages import HumanMessage
                resp = await self._llm.ainvoke([HumanMessage(content=prompt)])
                baseline_text = resp.content
            except Exception as e:
                baseline_text = f"Baseline general response for {request.question} (LLM offline)."
        else:
            baseline_text = (
                f"[Baseline LLM Output - No Retrieval]\n"
                f"Regarding '{request.question}': This is a standard topic in {request.target_role}. "
                f"Typically, this concept involves handling requests and managing protocols, though specific framework-verified guidelines and verified course citations are not available in baseline mode."
            )

        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return {
            "answer": baseline_text,
            "latency_ms": latency_ms
        }

    async def _generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        retrieved_results: List[Dict[str, Any]]
    ) -> (str, str):
        """Generates response via Gemini, LangChain LLM, or deterministic grounded fallback."""
        if self._llm == "gemini" and self._gemini_client:
            try:
                from google.genai import types
                combined_prompt = f"{system_prompt}\n\n{user_prompt}"
                config = types.GenerateContentConfig(
                    temperature=settings.LLM_TEMPERATURE,
                    response_mime_type="application/json"
                )
                response = self._gemini_client.models.generate_content(
                    model=settings.LLM_MODEL or "gemini-2.5-flash",
                    contents=combined_prompt,
                    config=config
                )
                raw_content = response.text.strip()
                if raw_content.startswith("```json"):
                    raw_content = raw_content[7:]
                if raw_content.endswith("```"):
                    raw_content = raw_content[:-3]
                raw_content = raw_content.strip()
                try:
                    parsed = json.loads(raw_content)
                    return parsed.get("answer", raw_content), parsed.get("recommended_next_topic", "Advanced Patterns")
                except json.JSONDecodeError:
                    return raw_content, "Advanced Architecture Patterns"
            except Exception as e:
                print(f"[Warning] Gemini generation failed: {e}. Using grounded context generator.")

        elif self._llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                response = await self._llm.ainvoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
                raw_content = response.content.strip()

                # Clean markdown JSON block if present
                if raw_content.startswith("```json"):
                    raw_content = raw_content[7:]
                if raw_content.endswith("```"):
                    raw_content = raw_content[:-3]
                raw_content = raw_content.strip()

                try:
                    parsed = json.loads(raw_content)
                    return parsed.get("answer", raw_content), parsed.get("recommended_next_topic", "Advanced Patterns")
                except json.JSONDecodeError:
                    return raw_content, "Advanced Architecture Patterns"
            except Exception as e:
                print(f"[Warning] LLM generation failed: {e}. Using grounded context generator.")

        # Grounded context-driven generator when offline or in test environment
        if retrieved_results:
            top_item = retrieved_results[0]
            answer = (
                f"Based on the official curriculum material from {top_item['source']} ('{top_item['title']}'):\n\n"
                f"{top_item['content']}\n\n"
                f"In industrial {top_item['target_role']} workflows, applying this knowledge ensures compliance with "
                f"production standards, reducing latency and security vulnerabilities."
            )
            next_topic = f"Advanced {top_item['topic']}: Security & Scaling"
        else:
            answer = "No grounded material found for this specific inquiry. Please refer to curriculum guidelines."
            next_topic = "Core Fundamentals"

        return answer, next_topic


learning_rag_service = LearningRAGService()
