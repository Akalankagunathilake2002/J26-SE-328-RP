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
    # The previous turn, so the interviewer can acknowledge the answer and follow up on gaps
    previous_question: Optional[str] = None
    previous_answer: Optional[str] = None
    previous_missing_concepts: List[str] = []
    # One-sentence background from the candidate's CV, used to tailor the question
    candidate_background: Optional[str] = Field(None, max_length=600)


class RoleInfo(BaseModel):
    role: str
    questions: int
    levels: Dict[str, int]              # e.g. {"Entry Level": 4, "Mid Level": 3}


class CVProfileResponse(BaseModel):
    name: str = ""
    skills: List[str]
    suggested_role: str
    experience_level: str
    summary: str = ""
    method: str                         # "llm" or "keyword"
    characters_read: int


class InterviewQuestionResponse(BaseModel):
    turn_id: str
    session_id: str
    question: str
    topic: str
    difficulty: str
    context_or_reason: str
    rubric_criteria: List[str]
    # Local-avatar clips for this question, one per sentence group, in playback order
    avatar_job_ids: List[str] = []


class TranscribeResponse(BaseModel):
    transcript: str
    latency_ms: float
    domain_terms_detected: Optional[List[str]] = []


class AvatarSessionTokenResponse(BaseModel):
    session_token: str
    session_id: str
    avatar_id: str
    is_sandbox: bool


class AvatarConfigResponse(BaseModel):
    provider: str                       # "liveavatar" | "local" | "none"
    available: bool
    avatar_name: Optional[str] = None
    idle_video_url: Optional[str] = None
    detail: Optional[str] = None


class AvatarRenderRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class AvatarRenderResponse(BaseModel):
    job_ids: List[str]                  # sentence clips in playback order


class AvatarCancelRequest(BaseModel):
    job_ids: List[str] = Field(default_factory=list, max_length=50)


class AvatarJobResponse(BaseModel):
    job_id: str
    status: str                         # "queued" | "running" | "done" | "error" | "cancelled"
    message: Optional[str] = None
    queued_ahead: Optional[int] = None
    video_url: Optional[str] = None
    audio_seconds: Optional[float] = None
    error: Optional[str] = None


class EvaluateAnswerRequest(BaseModel):
    turn_id: str
    transcript: str
    student_id: str
    speaking_duration_seconds: Optional[float] = Field(None, example=35.5)
    eye_contact_ratio: Optional[float] = Field(None, example=0.82)
    words_per_minute: Optional[float] = Field(None, example=135.0)
    filler_words_count: Optional[int] = Field(None, example=2)
    # Observable delivery cues measured in the browser (camera: MediaPipe face landmarks; mic:
    # loudness). Fractions are 0-1 of the answer's duration. No video or images leave the browser,
    # and no emotion or mood is inferred.
    face_visible_ratio: Optional[float] = Field(None, ge=0, le=1)
    smile_ratio: Optional[float] = Field(None, ge=0, le=1)
    brow_tension_ratio: Optional[float] = Field(None, ge=0, le=1)
    blink_rate_per_min: Optional[float] = Field(None, ge=0, le=200)
    head_steadiness: Optional[float] = Field(None, ge=0, le=1)
    pause_ratio: Optional[float] = Field(None, ge=0, le=1)


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
    speaking_duration_seconds: Optional[float] = None
    words_per_minute: Optional[float] = None
    eye_contact_ratio: Optional[float] = None
    pacing_assessment: Optional[str] = None
    overall_score: Optional[float] = None
    # What the interviewer says out loud after the answer, and its local-avatar clips (if any)
    spoken_feedback: Optional[str] = None
    avatar_job_ids: List[str] = []
    # How technical_accuracy was produced (llm / calibrated / trained / blend) and the LLM's own score
    scoring_method: str = "llm"
    llm_technical_accuracy: Optional[float] = None
