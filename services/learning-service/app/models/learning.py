import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, Float, String, Text, Integer, Numeric, DateTime, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from app.core.config import settings


class LearningDocument(Base):
    __tablename__ = "learning_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    source = Column(String(255), nullable=False)
    url = Column(Text, nullable=True)
    topic = Column(String(100), nullable=False)
    target_role = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_learning_docs_role_topic", "target_role", "topic"),
    )


class LearningChunk(Base):
    __tablename__ = "learning_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("learning_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_learning_chunks_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )


class StudentLearningSession(Base):
    __tablename__ = "student_learning_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(100), nullable=False, index=True)
    target_role = Column(String(100), nullable=False)
    session_title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class StudentLearningQuery(Base):
    __tablename__ = "student_learning_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("student_learning_sessions.id", ondelete="CASCADE"), nullable=True)
    student_id = Column(String(100), nullable=False, index=True)
    question = Column(Text, nullable=False)
    learning_priority = Column(String(100), nullable=True)
    answer = Column(Text, nullable=False)
    recommended_next_topic = Column(String(100), nullable=True)
    retrieved_chunk_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    sources = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class StudentTopicProgress(Base):
    __tablename__ = "student_topic_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(100), nullable=False)
    topic = Column(String(100), nullable=False)
    target_role = Column(String(100), nullable=False)
    queries_count = Column(Integer, default=1)
    status = Column(String(50), default="in_progress")  # in_progress, completed
    last_studied_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_student_topic_unique", "student_id", "topic", "target_role", unique=True),
    )


class LearningExperimentLog(Base):
    __tablename__ = "learning_experiment_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    top_k = Column(Integer, default=4)
    retrieval_strategy = Column(String(50), default="cosine_similarity")
    embedding_model = Column(String(100), nullable=False)
    llm_model = Column(String(100), nullable=False)
    retrieved_chunk_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    similarity_scores = Column(ARRAY(Numeric), nullable=True)
    retrieval_latency_ms = Column(Numeric(10, 2), nullable=True)
    generation_latency_ms = Column(Numeric(10, 2), nullable=True)
    total_latency_ms = Column(Numeric(10, 2), nullable=True)
    generated_output = Column(Text, nullable=False)
    is_baseline = Column(Integer, default=0) # 0 = proposed RAG, 1 = baseline direct LLM
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class RagBenchmarkRun(Base):
    """One run of the golden-dataset RAG benchmark (rag_evaluator.py): measured, never fixed values."""
    __tablename__ = "rag_benchmark_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, default="running")   # running, done, failed
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    items_done = Column(Integer, default=0)
    items_total = Column(Integer, default=0)
    results = Column(JSONB, nullable=True)       # summary per strategy, significance, per-item rows
    error = Column(Text, nullable=True)


class EduLessonCache(Base):
    """Generated Skillaro lessons, reused for the next student who asks for the same topic and stage."""
    __tablename__ = "edu_lesson_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_role = Column(String(100), nullable=False)
    topic = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)
    lesson = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_edu_lesson_cache_key", "target_role", "topic", "level", unique=True),
    )


class EduMastery(Base):
    """A finished Skillaro check (quiz) for one topic and stage: the student's mastery record."""
    __tablename__ = "edu_mastery"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(100), nullable=False, index=True)
    topic = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)
    mcq_correct = Column(Integer, nullable=False, default=0)
    mcq_total = Column(Integer, nullable=False, default=0)
    open_score = Column(Float, nullable=True)       # average mark 0-100 of written answers, if any were marked
    completed_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class EduReviewItem(Base):
    """A missed quiz question scheduled for spaced repetition (Leitner boxes: 1, 3, 7 days)."""
    __tablename__ = "edu_review_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(100), nullable=False, index=True)
    topic = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)
    question = Column(JSONB, nullable=False)        # the MCQ as it was asked
    box = Column(Integer, nullable=False, default=0)
    due_at = Column(DateTime(timezone=True), nullable=False)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    done = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
