from enum import StrEnum

from pydantic import BaseModel, Field


class MatchMethod(StrEnum):
    """How a term was mapped to a skill (TAF task 5), from most to least certain."""

    EXACT = "exact"                    # a dictionary name or alias as written
    CLEANED = "cleaned"                # after removing versions and suffixes ("Python3", "ReactJS")
    FUZZY = "fuzzy"                    # spelling mistake ("Javascrpit")
    SEMANTIC = "semantic"              # same meaning, other words ("made neural networks")
    ESCO_CANDIDATE = "esco_candidate"  # not in SSKS, but close to an ESCO skill: new-skill candidate
    UNMATCHED = "unmatched"


class Candidate(BaseModel):
    skill_id: str
    name: str
    score: float


class NormalisedTerm(BaseModel):
    term: str
    skill_id: str | None
    name: str | None
    method: MatchMethod
    score: float = Field(description="Match score 0-1: 1 exact, edit similarity, or cosine")
    candidates: list[Candidate] = Field(default_factory=list,
                                        description="Semantic candidates considered, best first")


class NormaliseRequest(BaseModel):
    terms: list[str] = Field(min_length=1, max_length=200)
