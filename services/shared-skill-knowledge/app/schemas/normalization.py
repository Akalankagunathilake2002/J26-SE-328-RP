from typing import Literal
from pydantic import BaseModel, Field

NormalizationStatus = Literal["MATCHED", "SUGGESTED", "UNMATCHED"]
MatchingMethod = Literal["CANONICAL_NAME", "VERIFIED_ALIAS", "FUZZY_SUGGESTION"]

class SuggestedMatch(BaseModel):
    canonical_id: str
    preferred_name: str
    score: float

class NormalizeResultItem(BaseModel):
    input_name: str
    status: NormalizationStatus
    canonical_id: str | None = None
    preferred_name: str | None = None
    matching_method: MatchingMethod | None = None
    suggestions: list[SuggestedMatch] = Field(default_factory=list)

class BulkNormalizeRequest(BaseModel):
    items: list[str] = Field(..., min_length=1, max_length=500, description="List of skill or role names to normalize")

class BulkNormalizeResponse(BaseModel):
    results: list[NormalizeResultItem]
