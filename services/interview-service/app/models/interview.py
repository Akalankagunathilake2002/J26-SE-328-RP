import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Numeric, DateTime, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from app.core.config import settings


class InterviewDocument(Base):
    __tablename__ = "interview_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False, index=True)
    topic = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=False)  # Entry Level, Mid, Senior
    source = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_interview_docs_role_diff", "role", "difficulty"),
    )


class InterviewChunk(Base):
    __tablename__ = "interview_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("interview_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=True)
    rubric = Column(JSONB, nullable=False, default=dict)
    chunk_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_interview_chunks_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(100), nullable=False, index=True)
    target_role = Column(String(100), nullable=False)
    experience_level = Column(String(50), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    topic = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=False)
    transcript = Column(Text, nullable=True)
    technical_accuracy_score = Column(Numeric(3, 2), nullable=True)
    relevance_score = Column(Numeric(3, 2), nullable=True)
    explanation_quality_score = Column(Numeric(3, 2), nullable=True)
    clarity_score = Column(Numeric(3, 2), nullable=True)
    technical_feedback = Column(Text, nullable=True)
    communication_feedback = Column(Text, nullable=True)
    missing_concepts = Column(JSONB, nullable=True)
    strengths = Column(JSONB, nullable=True)
    areas_for_improvement = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class InterviewExperimentLog(Base):
    __tablename__ = "interview_experiment_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turn_id = Column(UUID(as_uuid=True), ForeignKey("interview_turns.id", ondelete="CASCADE"), nullable=True)
    stt_latency_ms = Column(Numeric(10, 2), nullable=True)
    retrieval_latency_ms = Column(Numeric(10, 2), nullable=True)
    evaluation_latency_ms = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
