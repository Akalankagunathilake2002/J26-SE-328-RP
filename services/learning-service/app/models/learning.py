import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Numeric, DateTime, ForeignKey, Index
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
