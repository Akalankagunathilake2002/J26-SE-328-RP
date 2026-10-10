import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.learning import LearningExperimentLog
from app.core.config import settings


class ExperimentLogger:
    @staticmethod
    async def log_run(
        session: AsyncSession,
        query_text: str,
        retrieved_chunk_ids: List[str],
        similarity_scores: List[float],
        retrieval_latency_ms: float,
        generation_latency_ms: float,
        generated_output: str,
        is_baseline: int = 0
    ) -> uuid.UUID:
        """Logs experimental run metrics for academic evaluation and research papers."""
        log_entry = LearningExperimentLog(
            query_text=query_text,
            top_k=settings.TOP_K,
            retrieval_strategy="cosine_similarity",
            embedding_model=settings.EMBEDDING_MODEL_NAME,
            llm_model=settings.LLM_MODEL,
            retrieved_chunk_ids=[uuid.UUID(cid) for cid in retrieved_chunk_ids if cid],
            similarity_scores=similarity_scores,
            retrieval_latency_ms=retrieval_latency_ms,
            generation_latency_ms=generation_latency_ms,
            total_latency_ms=retrieval_latency_ms + generation_latency_ms,
            generated_output=generated_output,
            is_baseline=is_baseline
        )
        session.add(log_entry)
        await session.commit()
        return log_entry.id


experiment_logger = ExperimentLogger()
