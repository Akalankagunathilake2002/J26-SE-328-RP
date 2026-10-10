from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    student_id: str = Field(..., example="stu_1024")
    target_role: str = Field(..., example="Backend Developer")
    experience_level: str = Field(default="Entry Level", example="Entry Level")
    current_skills: List[str] = Field(default_factory=list, example=["Java", "Spring Boot", "MySQL"])


class InterviewSessionResponse(BaseModel):
    session_id: str
    student_id: str
    target_role: str
    experience_level: str
    message: str


class QuestionGenerationRequest(BaseModel):
    session_id: str
    student_id: str
    target_role: str
    experience_level: str = "Entry Level"
    current_skills: List[str] = []
    preferred_topic: Optional[str] = None


class InterviewQuestionResponse(BaseModel):
    turn_id: str
    session_id: str
    question: str
    topic: str
    difficulty: str
    context_or_reason: str
    rubric_criteria: List[str]


class TranscribeResponse(BaseModel):
    transcript: str
    latency_ms: float


class EvaluateAnswerRequest(BaseModel):
    turn_id: str
    transcript: str
    student_id: str


class EvaluationResultResponse(BaseModel):
    turn_id: str
    technical_accuracy: float = Field(..., ge=1.0, le=5.0)
    relevance: float = Field(..., ge=1.0, le=5.0)
    explanation_quality: float = Field(..., ge=1.0, le=5.0)
    clarity: float = Field(..., ge=1.0, le=5.0)
    technical_feedback: str
    communication_feedback: str
    missing_concepts: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]
    evaluation_latency_ms: float
