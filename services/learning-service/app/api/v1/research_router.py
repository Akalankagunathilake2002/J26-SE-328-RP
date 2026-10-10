from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.learning import LearningExperimentLog
from app.schemas.learning import (
    BenchmarkRequest,
    BenchmarkComparisonResponse,
    LearningQueryRequest,
    RetrievalAblationResponse,
    RetrievalStrategyResult,
    RetrievedChunkDebug
)
from app.services.learning_rag import learning_rag_service
from app.services.experiment_logger import experiment_logger
from app.services.vector_store import vector_store_service

router = APIRouter(prefix="/research", tags=["Research & Viva Evaluation"])


class RetrievalAblationRequest(BaseModel):
    question: str = "How does JWT authentication work?"
    target_role: Optional[str] = "Backend Developer"
    top_k: int = 4


@router.post("/retrieval-ablation", response_model=RetrievalAblationResponse)
async def run_retrieval_ablation(
    request: RetrievalAblationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes a multi-strategy retrieval ablation:
    1. Dense Semantic Vector Search (pgvector HNSW)
    2. Sparse Lexical BM25 Search (PostgreSQL GIN tsvector)
    3. Hybrid Reciprocal Rank Fusion (RRF)
    
    Returns side-by-side chunks, latencies, Jaccard similarity, and rank agreement.
    """
    try:
        raw = await vector_store_service.run_retrieval_ablation(
            session=db,
            query=request.question,
            target_role=request.target_role,
            top_k=request.top_k
        )

        def to_chunk_debug(c: Dict[str, Any]) -> RetrievedChunkDebug:
            return RetrievedChunkDebug(
                chunk_id=c["chunk_id"],
                content_preview=c["content"][:200] + ("..." if len(c["content"]) > 200 else ""),
                similarity_score=c["similarity_score"],
                source=c["source"],
                topic=c["topic"],
                dense_rank=c.get("dense_rank"),
                sparse_rank=c.get("sparse_rank"),
                rrf_score=c.get("rrf_score"),
                retrieval_method=c.get("retrieval_method")
            )

        dense_res = RetrievalStrategyResult(
            strategy=raw["dense"]["strategy"],
            latency_ms=raw["dense"]["latency_ms"],
            retrieved_count=raw["dense"]["count"],
            top_chunks=[to_chunk_debug(c) for c in raw["dense"]["chunks"]],
            top_topics=raw["dense"]["topics"]
        )

        sparse_res = RetrievalStrategyResult(
            strategy=raw["sparse"]["strategy"],
            latency_ms=raw["sparse"]["latency_ms"],
            retrieved_count=raw["sparse"]["count"],
            top_chunks=[to_chunk_debug(c) for c in raw["sparse"]["chunks"]],
            top_topics=raw["sparse"]["topics"]
        )

        hybrid_res = RetrievalStrategyResult(
            strategy=raw["hybrid"]["strategy"],
            latency_ms=raw["hybrid"]["latency_ms"],
            retrieved_count=raw["hybrid"]["count"],
            top_chunks=[to_chunk_debug(c) for c in raw["hybrid"]["chunks"]],
            top_topics=raw["hybrid"]["topics"]
        )

        return RetrievalAblationResponse(
            question=raw["query"],
            target_role=raw["target_role"],
            dense_results=dense_res,
            sparse_results=sparse_res,
            hybrid_results=hybrid_res,
            jaccard_overlap_dense_sparse=raw["jaccard_overlap_dense_sparse"],
            hybrid_dense_agreement=raw["hybrid_dense_agreement"],
            hybrid_sparse_agreement=raw["hybrid_sparse_agreement"],
            recommended_strategy="hybrid_rrf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval ablation error: {str(e)}")


@router.post("/benchmark", response_model=BenchmarkComparisonResponse)
async def run_benchmark_comparison(
    request: BenchmarkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes an ablation experiment comparing Baseline (Direct LLM) vs. Proposed (pgvector RAG).
    Logs telemetry for research evaluation and displays side-by-side in the Viva Debug View.
    """
    try:
        query_req = LearningQueryRequest(
            student_id=request.student_id,
            target_role=request.target_role,
            current_skills=request.current_skills,
            learning_priority=request.learning_priority,
            question=request.question
        )

        # 1. Run Baseline Condition
        baseline_result = await learning_rag_service.execute_baseline(query_req)

        # Log baseline
        await experiment_logger.log_run(
            session=db,
            query_text=request.question,
            retrieved_chunk_ids=[],
            similarity_scores=[],
            retrieval_latency_ms=0.0,
            generation_latency_ms=baseline_result["latency_ms"],
            generated_output=baseline_result["answer"],
            is_baseline=1
        )

        # 2. Run Proposed RAG Condition
        rag_response = await learning_rag_service.execute_rag(session=db, request=query_req)

        # Log RAG
        await experiment_logger.log_run(
            session=db,
            query_text=request.question,
            retrieved_chunk_ids=[c.chunk_id for c in rag_response.retrieved_chunks],
            similarity_scores=[c.similarity_score for c in rag_response.retrieved_chunks],
            retrieval_latency_ms=rag_response.retrieval_latency_ms,
            generation_latency_ms=rag_response.generation_latency_ms,
            generated_output=rag_response.answer,
            is_baseline=0
        )

        return BenchmarkComparisonResponse(
            question=request.question,
            baseline_answer=baseline_result["answer"],
            baseline_latency_ms=baseline_result["latency_ms"],
            rag_answer=rag_response.answer,
            rag_sources=rag_response.sources,
            rag_retrieved_chunks=rag_response.retrieved_chunks,
            rag_latency_ms=rag_response.total_latency_ms,
            recommended_next_topic=rag_response.recommended_next_topic
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark execution error: {str(e)}")


@router.get("/experiments")
async def list_recent_experiments(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Fetches recent experimental runs for thesis data collection."""
    stmt = select(LearningExperimentLog).order_by(LearningExperimentLog.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "id": str(r.id),
            "query": r.query_text,
            "is_baseline": bool(r.is_baseline),
            "retrieval_latency_ms": float(r.retrieval_latency_ms or 0),
            "generation_latency_ms": float(r.generation_latency_ms or 0),
            "total_latency_ms": float(r.total_latency_ms or 0),
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in records
    ]
