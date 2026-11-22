from typing import List, Optional, Dict, Any, Literal
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
    # None for the no-retrieval baseline: there is no context for its claims to be grounded in
    faithfulness: Optional[float] = Field(None, description="Proportion of claims grounded in retrieved context (0.0 to 1.0)")
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
    # Paired permutation test, advanced vs naive RAG on per-query faithfulness (None if not computable)
    p_value_statistical_significance: Optional[float] = None
    research_conclusion: str
    # The run these numbers come from (rag_benchmark_runs)
    run_id: Optional[str] = None
    run_finished_at: Optional[str] = None
    compression_saved_percent: Optional[float] = None
    method_notes: Optional[str] = None


class BenchmarkRunStatus(BaseModel):
    run_id: Optional[str] = None
    status: str                       # none, running, done, failed
    items_done: int = 0
    items_total: int = 0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None


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


class LearningTopic(BaseModel):
    title: str
    topic: str
    target_role: str


# ---------------------------------------------------------------- Skillaro Edu Assistant
LessonLevel = Literal["beginner", "intermediate", "advanced"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=6000)


class EduChatRequest(BaseModel):
    student_id: str
    target_role: str
    current_skills: List[str] = Field(default_factory=list)
    learning_priority: Optional[str] = None
    student_name: Optional[str] = Field(None, max_length=100)
    message: str = Field(..., min_length=1, max_length=2000)
    # Earlier turns of this conversation, oldest first (the last few are used)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)
    # The topic of the lesson in progress, if any, so follow-up questions stay on it
    current_topic: Optional[str] = Field(None, max_length=100)


class EduChatResponse(BaseModel):
    reply: str
    # Curriculum topics Skillaro suggests learning next (names the lesson endpoint accepts)
    suggested_topics: List[str] = []
    sources: List[SourceCitation] = []
    latency_ms: float


class LessonRequest(BaseModel):
    student_id: str
    target_role: str
    current_skills: List[str] = Field(default_factory=list)
    topic: str = Field(..., min_length=2, max_length=100)
    level: LessonLevel = "beginner"
    # Write a new lesson instead of reusing the cached one for this role, topic and stage
    fresh: bool = False


class LessonSection(BaseModel):
    heading: str
    body: str


class LessonResponse(BaseModel):
    topic: str
    level: LessonLevel
    bloom_levels: List[str]             # the Bloom's taxonomy levels this stage teaches and checks
    title: str
    introduction: str
    sections: List[LessonSection]
    key_points: List[str]
    example: Optional[str] = None
    sources: List[SourceCitation] = []
    latency_ms: float
    cached: bool = False


class QuizRequest(BaseModel):
    student_id: str
    target_role: str
    topic: str = Field(..., min_length=2, max_length=100)
    level: LessonLevel = "beginner"
    # The lesson's key points, so the questions test what was taught
    key_points: List[str] = Field(default_factory=list, max_length=12)


class MultipleChoiceQuestion(BaseModel):
    question: str
    options: List[str]                  # four options
    answer_index: int
    explanation: str
    bloom_level: str


class OpenQuestion(BaseModel):
    question: str
    bloom_level: str
    guidance: str                       # what a good answer covers (shown after answering)


class QuizResponse(BaseModel):
    topic: str
    level: LessonLevel
    mcqs: List[MultipleChoiceQuestion]
    open_questions: List[OpenQuestion]
    latency_ms: float


class GradeAnswerRequest(BaseModel):
    student_id: str
    target_role: str
    topic: str = Field(..., max_length=100)
    level: LessonLevel = "beginner"
    question: str = Field(..., max_length=1000)
    bloom_level: str = Field(..., max_length=20)
    guidance: str = Field("", max_length=1500)
    answer: str = Field(..., min_length=1, max_length=4000)


class GradeAnswerResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)
    verdict: Literal["excellent", "good", "partial", "needs_work"]
    feedback: str
    model_answer: str



# ---------------------------------------------------------------- Skillaro mastery and spaced repetition
class MasteryRecordRequest(BaseModel):
    student_id: str
    topic: str = Field(..., min_length=2, max_length=100)
    level: LessonLevel
    mcq_correct: int = Field(..., ge=0)
    mcq_total: int = Field(..., ge=0)
    open_score: Optional[float] = Field(None, ge=0, le=100)
    # Questions answered wrongly: scheduled for review after 1, 3 and 7 days
    missed_mcqs: List[MultipleChoiceQuestion] = Field(default_factory=list, max_length=10)


class MasteryEntry(BaseModel):
    topic: str
    level: LessonLevel
    attempts: int
    best_percent: int                 # best MCQ score, 0-100
    open_score: Optional[float] = None
    mastered: bool                    # best MCQ score at least 60%
    last_at: str


class MasteryResponse(BaseModel):
    student_id: str
    entries: List[MasteryEntry]
    reviews_due: int = 0


class ReviewItem(BaseModel):
    id: str
    topic: str
    level: LessonLevel
    question: MultipleChoiceQuestion
    box: int
    due_at: str


class ReviewAnswerRequest(BaseModel):
    correct: bool


class ReviewAnswerResponse(BaseModel):
    id: str
    done: bool
    box: int
    next_due_at: Optional[str] = None
