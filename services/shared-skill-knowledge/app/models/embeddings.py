from datetime import datetime, timezone
import json
from typing import Any
from sqlalchemy import CHAR, CheckConstraint, DateTime, ForeignKey, Index, SmallInteger, String, Text, TypeDecorator, func, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import cast as sa_cast
from sqlalchemy.types import UserDefinedType

from app.db.base import Base


class VectorPGType(UserDefinedType):
    """PostgreSQL pgvector column mapping without requiring a separate pgvector package."""

    cache_ok = True

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **kw: Any) -> str:
        return f"vector({self.dimensions})"

    def bind_expression(self, bindvalue):
        return sa_cast(bindvalue, self)


class VectorType(TypeDecorator):
    """Stores 384-d float vectors as pgvector on PostgreSQL and JSON text on SQLite."""

    impl = Text
    cache_ok = True

    def __init__(self, dimensions: int = 384) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(VectorPGType(self.dimensions))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return "[" + ",".join(repr(float(x)) for x in value) + "]"

    def process_result_value(self, value: Any, dialect) -> list[float] | None:
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        return [float(x) for x in json.loads(str(value))]


class SkillEmbedding(Base):
    __tablename__ = "skill_embeddings"

    skill_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    )
    embedding_model: Mapped[str] = mapped_column(String(150), primary_key=True)
    embedding_dimension: Mapped[int] = mapped_column(SmallInteger, default=384, server_default=text("384"))
    embedding_text_hash: Mapped[str] = mapped_column(CHAR(64))
    embedding: Mapped[list[float]] = mapped_column(VectorType(384))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint("embedding_dimension = 384", name="chk_skill_embedding_dimension"),
        Index("idx_skill_embeddings_model", "embedding_model"),
    )
