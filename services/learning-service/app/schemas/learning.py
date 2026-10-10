from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StudentProfileContext(BaseModel):
    student_id: str = Field(..., example="stu_1024")
    target_role: str = Field(..., example="Backend Developer")
    current_skills: List[str] = Field(default_factory=list, example=["Python", "SQL", "Git"])
    learning_priority: Optional[str] = Field(None, example="REST API Development")


class LearningQueryRequest(BaseModel):
    student_id: str = Field(..., example="stu_1024")
    target_role: str = Field(..., example="Backend Developer")
    current_skills: List[str] = Field(default_factory=list, example=["Python", "SQL", "Git"])
    learning_priority: Optional[str] = Field(None, example="REST API Development")
    question: str = Field(..., example="How does JWT authentication work?")
    session_id: Optional[str] = None


class SourceCitation(BaseModel):
    title: str
    source: str
    url: Optional[str] = None
    topic: Optional[str] = None


class RetrievedChunkDebug(BaseModel):
    chunk_id: str
    content_preview: str
    similarity_score: float
    source: str
    topic: str
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    rrf_score: Optional[float] = None
    retrieval_method: Optional[str] = "hybrid_rrf"


class LearningQueryResponse(BaseModel):
    answer: str
    recommended_next_topic: str
    sources: List[SourceCitation]
    retrieved_chunks: List[RetrievedChunkDebug]
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    retrieval_strategy: Optional[str] = "hybrid_rrf"


class BenchmarkRequest(BaseModel):
    student_id: str = "benchmark_user"
    target_role: str = "Backend Developer"
    current_skills: List[str] = ["Python", "SQL"]
    learning_priority: str = "REST API Security"
    question: str = "How does JWT authentication work?"


class BenchmarkComparisonResponse(BaseModel):
    question: str
    baseline_answer: str
    baseline_latency_ms: float
    rag_answer: str
    rag_sources: List[SourceCitation]
    rag_retrieved_chunks: List[RetrievedChunkDebug]
    rag_latency_ms: float
    recommended_next_topic: str
    retrieval_strategy: Optional[str] = "hybrid_rrf"


class RetrievalStrategyResult(BaseModel):
    strategy: str  # dense_only, sparse_only, hybrid_rrf
    latency_ms: float
    retrieved_count: int
    top_chunks: List[RetrievedChunkDebug]
    top_topics: List[str]


class RetrievalAblationResponse(BaseModel):
    question: str
    target_role: str
    dense_results: RetrievalStrategyResult
    sparse_results: RetrievalStrategyResult
    hybrid_results: RetrievalStrategyResult
    jaccard_overlap_dense_sparse: float
    hybrid_dense_agreement: float
    hybrid_sparse_agreement: float
    recommended_strategy: str = "hybrid_rrf"
