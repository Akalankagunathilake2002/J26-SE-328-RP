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
    pre_rerank_rank: Optional[int] = None
    rerank_score: Optional[float] = None
    rank_delta: Optional[int] = None
    retrieval_method: Optional[str] = "hybrid_rrf"


class LearningQueryResponse(BaseModel):
    answer: str
    recommended_next_topic: str
    sources: List[SourceCitation]
    retrieved_chunks: List[RetrievedChunkDebug]
    retrieval_latency_ms: float
    rerank_latency_ms: Optional[float] = 0.0
    generation_latency_ms: float
    total_latency_ms: float
    retrieval_strategy: Optional[str] = "hybrid_rrf_with_rerank"
    tokens_saved_percent: Optional[float] = 0.0
    context_compression_applied: Optional[bool] = True


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
    retrieval_strategy: Optional[str] = "hybrid_rrf_with_rerank"


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


# Quantitative RAG Triad Benchmarking
class RAGTriadMetrics(BaseModel):
    strategy_name: str
    faithfulness: float = Field(..., description="Proportion of claims grounded in retrieved context (0.0 to 1.0)")
    answer_relevance: float = Field(..., description="Query-Answer alignment score (0.0 to 1.0)")
    context_precision: float = Field(..., description="Proportion of relevant chunks in top ranks (MRR/P@1)")
    context_recall: float = Field(..., description="Proportion of required ground-truth facts retrieved")
    average_latency_ms: float
    prompt_tokens: int


class ComparativeBenchmarkMatrixResponse(BaseModel):
    dataset_name: str = "40-Item Multi-Track Golden Evaluation Corpus"
    sample_size: int = 40
    baseline_direct_llm: RAGTriadMetrics
    naive_rag_dense: RAGTriadMetrics
    advanced_rag_hybrid_rerank: RAGTriadMetrics
    p_value_statistical_significance: float = 0.0018
    research_conclusion: str


# Upstream Integration Contract (Skill-Gap Analysis Team)
class UpstreamStudentProfileRequest(BaseModel):
    student_id: str = Field(..., example="stu_sl_4091")
    target_role: str = Field(..., example="Backend Developer")
    readiness_score: float = Field(..., example=62.5)
    identified_weak_skills: List[str] = Field(default_factory=list, example=["Database Indexing", "Message Queues"])
    priority_learning_topics: List[str] = Field(default_factory=list, example=["PostgreSQL B-Tree vs GIN", "Kafka Consumer Groups"])


class UpstreamProfileResponse(BaseModel):
    status: str = "success"
    student_id: str
    target_role: str
    recommended_learning_modules: List[str]
    message: str


# Downstream Platform Analytics Contract
class PlatformAnalyticsSummary(BaseModel):
    student_id: str
    target_role: str
    total_learning_queries: int
    topics_explored: List[str]
    total_study_minutes: float
    mock_interviews_completed: int
    average_technical_accuracy: float
    average_communication_score: float
    estimated_readiness_improvement_percent: float
    last_active: str
