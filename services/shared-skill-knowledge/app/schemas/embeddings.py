from datetime import datetime
import math
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


Hash64 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=64, max_length=64)]
ModelName150 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]


class SkillEmbeddingSummaryOut(BaseModel):
    skill_id: str
    embedding_model: str
    embedding_dimension: int
    embedding_text_hash: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillEmbeddingOut(SkillEmbeddingSummaryOut):
    embedding: list[float]


class SkillEmbeddingUpsert(BaseModel):
    embedding_model: ModelName150
    embedding_text_hash: Hash64
    embedding: list[float] = Field(..., min_length=384, max_length=384)

    @field_validator("embedding")
    @classmethod
    def validate_finite_vector(cls, values: list[float]) -> list[float]:
        for val in values:
            if not math.isfinite(val):
                raise ValueError("Embedding vector must contain only finite floats")
        return values
