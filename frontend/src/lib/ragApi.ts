// RAG API Client for Academic-to-Industry Skill Bridge Platform

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export interface LearningQueryPayload {
  student_id: string;
  target_role: string;
  current_skills: string[];
  learning_priority: string;
  question: string;
}

export interface SourceCitation {
  title: string;
  source: string;
  url?: string;
  topic?: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  title?: string;
  content_preview: string;
  similarity_score: number;
  source: string;
  topic: string;
  dense_rank?: number;
  sparse_rank?: number;
  rrf_score?: number;
  pre_rerank_rank?: number;
  rerank_score?: number;
  rank_delta?: number;
  retrieval_method?: string;
}

export interface LearningResponse {
  answer: string;
  recommended_next_topic: string;
  sources: SourceCitation[];
  retrieved_chunks: RetrievedChunk[];
  retrieval_latency_ms: number;
  rerank_latency_ms?: number;
  generation_latency_ms: number;
  total_latency_ms: number;
  retrieval_strategy?: string;
  tokens_saved_percent?: number;
  context_compression_applied?: boolean;
}

/** A curriculum document the learning assistant can ground answers in */
export interface LearningTopic {
  title: string;
  topic: string;
  target_role: string;
}

export interface BenchmarkResponse {
  question: string;
  baseline_answer: string;
  baseline_latency_ms: number;
  rag_answer: string;
  rag_sources: SourceCitation[];
  rag_retrieved_chunks: RetrievedChunk[];
  rag_latency_ms: number;
  recommended_next_topic: string;
  retrieval_strategy?: string;
}

export interface RetrievalStrategyResult {
  strategy: string;
  latency_ms: number;
  retrieved_count: number;
  top_chunks: RetrievedChunk[];
  top_topics: string[];
}

export interface RetrievalAblationData {
  question: string;
  target_role: string;
  dense_results: RetrievalStrategyResult;
  sparse_results: RetrievalStrategyResult;
  hybrid_results: RetrievalStrategyResult;
  jaccard_overlap_dense_sparse: number;
  hybrid_dense_agreement: number;
  hybrid_sparse_agreement: number;
  recommended_strategy: string;
}

export interface RAGTriadMetrics {
  strategy_name: string;
  faithfulness: number;
  answer_relevance: number;
  context_precision: number;
  context_recall: number;
  average_latency_ms: number;
  prompt_tokens: number;
}

export interface ComparativeBenchmarkMatrixData {
  dataset_name: string;
  sample_size: number;
  baseline_direct_llm: RAGTriadMetrics;
  naive_rag_dense: RAGTriadMetrics;
  advanced_rag_hybrid_rerank: RAGTriadMetrics;
  p_value_statistical_significance: number;
  research_conclusion: string;
}

export interface GoldenDatasetItem {
  id: string;
  track: string;
  target_role: string;
  topic: string;
  query: string;
  ground_truth_doc_title: string;
  ground_truth_keywords: string[];
  expert_reference_answer: string;
}

export interface InterviewSession {
  session_id: string;
  student_id: string;
  target_role: string;
  experience_level: string;
  current_skills: string[];
  status: string;
}

export interface InterviewQuestionResponse {
  turn_id: string;
  question_number: number;
  topic: string;
  difficulty: string;
  question: string;
  rubric_criteria: string[];
  context_or_reason?: string;
  /** Local-avatar sentence clips already rendering for this question, in playback order */
  avatar_job_ids?: string[];
}

export interface EvaluationResponse {
  turn_id: string;
  technical_accuracy: number;
  relevance: number;
  explanation_quality: number;
  clarity: number;
  technical_feedback: string;
  communication_feedback: string;
  strengths: string[];
  missing_concepts: string[];
  areas_for_improvement?: string[];
  evaluation_latency_ms: number;
  speaking_duration_seconds?: number;
  words_per_minute?: number;
  eye_contact_ratio?: number;
  pacing_assessment?: string;
  overall_score?: number;
  /** What the interviewer says out loud after the answer */
  spoken_feedback?: string | null;
  /** Local-avatar sentence clips of spoken_feedback, already rendering, in playback order */
  avatar_job_ids?: string[];
}

export interface UpstreamProfilePayload {
  student_id: string;
  target_role: string;
  readiness_score: number;
  identified_weak_skills: string[];
  priority_learning_topics: string[];
}

export interface PlatformAnalyticsData {
  student_id: string;
  target_role: string;
  total_learning_queries: number;
  topics_explored: string[];
  total_study_minutes: number;
  mock_interviews_completed: number;
  average_technical_accuracy: number;
  average_communication_score: number;
  estimated_readiness_improvement_percent: number;
  last_active: string;
}

export interface AvatarSessionToken {
  session_token: string;
  session_id: string;
  avatar_id: string;
  is_sandbox: boolean;
}

export interface AvatarConfig {
  provider: "liveavatar" | "local" | "none";
  available: boolean;
  avatar_name?: string | null;
  idle_video_url?: string | null;
  detail?: string | null;
}

export interface AvatarJob {
  job_id: string;
  status: "queued" | "running" | "done" | "error" | "cancelled";
  message?: string | null;
  queued_ahead?: number | null;
  video_url?: string | null;
  audio_seconds?: number | null;
  error?: string | null;
}

/** Context from the previous turn (follow-ups) and the candidate's CV (tailoring) */
export interface PreviousTurnContext {
  previous_question?: string;
  previous_answer?: string;
  previous_missing_concepts?: string[];
  candidate_background?: string;
}

export interface RoleInfo {
  role: string;
  questions: number;
  levels: Record<string, number>;
}

export interface CVProfile {
  name: string;
  skills: string[];
  suggested_role: string;
  experience_level: string;
  summary: string;
  method: "llm" | "keyword";
  characters_read: number;
}

/** Observable delivery cues measured in the browser (camera + mic); no emotions are inferred */
export interface DeliveryTelemetry {
  speaking_duration_seconds?: number;
  words_per_minute?: number;
  filler_words_count?: number;
  pause_ratio?: number;
  eye_contact_ratio?: number;
  face_visible_ratio?: number;
  smile_ratio?: number;
  brow_tension_ratio?: number;
  blink_rate_per_min?: number;
  head_steadiness?: number;
}

export interface InterviewReport {
  session_id: string;
  questions_asked: number;
  turns_completed: number;
  overall_scores: { technical_accuracy: number; relevance: number; explanation_quality: number; clarity: number };
  turns: {
    turn_id: string;
    question: string;
    topic: string;
    transcript: string | null;
    evaluated: boolean;
    technical_accuracy: number | null;
    relevance: number | null;
    explanation_quality: number | null;
    clarity: number | null;
    strengths: string[];
    missing_concepts: string[];
    areas_for_improvement: string[];
  }[];
}

/** Prefer the backend's own explanation (FastAPI `detail`) over the bare status text */
async function apiError(res: Response, label: string): Promise<Error> {
  try {
    const body = await res.json();
    if (body?.detail) return new Error(typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail));
  } catch {
    /* not JSON */
  }
  return new Error(`${label}: ${res.statusText || res.status}`);
}

/** Absolute URL for a path the backend returns (avatar media is served through the gateway) */
export const apiUrl = (path: string) => (path.startsWith("http") ? path : `${API_BASE}${path}`);

export const ragApi = {
  async askLearning(payload: LearningQueryPayload): Promise<LearningResponse> {
    const res = await fetch(`${API_BASE}/api/v1/learning/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw await apiError(res, "Learning assistant error");
    }
    return res.json();
  },

  async getLearningTopics(targetRole: string): Promise<LearningTopic[]> {
    const res = await fetch(`${API_BASE}/api/v1/learning/topics?target_role=${encodeURIComponent(targetRole)}`);
    if (!res.ok) {
      throw await apiError(res, "Learning topics error");
    }
    return res.json();
  },

  async runBenchmark(payload: LearningQueryPayload): Promise<BenchmarkResponse> {
    const res = await fetch(`${API_BASE}/api/v1/research/benchmark`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(`Benchmark API error: ${res.statusText}`);
    }
    return res.json();
  },

  async runRetrievalAblation(payload: { question: string; target_role?: string; top_k?: number }): Promise<RetrievalAblationData> {
    const res = await fetch(`${API_BASE}/api/v1/research/retrieval-ablation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(`Retrieval ablation API error: ${res.statusText}`);
    }
    return res.json();
  },

  async fetchBenchmarkMatrix(): Promise<ComparativeBenchmarkMatrixData> {
    const res = await fetch(`${API_BASE}/api/v1/research/benchmark-matrix`);
    if (!res.ok) {
      throw new Error(`Benchmark Matrix API error: ${res.statusText}`);
    }
    return res.json();
  },

  async fetchGoldenDataset(): Promise<GoldenDatasetItem[]> {
    const res = await fetch(`${API_BASE}/api/v1/research/golden-dataset`);
    if (!res.ok) {
      throw new Error(`Golden Dataset API error: ${res.statusText}`);
    }
    return res.json();
  },

  async evaluateGoldenQuery(itemId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/research/evaluate-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: itemId }),
    });
    if (!res.ok) {
      throw new Error(`Evaluate query error: ${res.statusText}`);
    }
    return res.json();
  },

  async submitUpstreamProfile(payload: UpstreamProfilePayload): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/upstream/student-profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(`Upstream profile sync error: ${res.statusText}`);
    }
    return res.json();
  },

  async fetchPlatformAnalytics(studentId: string): Promise<PlatformAnalyticsData> {
    const res = await fetch(`${API_BASE}/api/v1/analytics/student-progress/${studentId}`);
    if (!res.ok) {
      throw new Error(`Analytics API error: ${res.statusText}`);
    }
    return res.json();
  },

  async getProgress(studentId: string) {
    const res = await fetch(`${API_BASE}/api/v1/progress/${studentId}`);
    if (!res.ok) {
      throw new Error(`Progress API error: ${res.statusText}`);
    }
    return res.json();
  },

  async startInterview(studentId: string, role: string, level: string, skills: string[]): Promise<InterviewSession> {
    const res = await fetch(`${API_BASE}/api/v1/interview/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: studentId,
        target_role: role,
        experience_level: level,
        current_skills: skills,
      }),
    });
    if (!res.ok) {
      throw new Error(`Interview start error: ${res.statusText}`);
    }
    return res.json();
  },

  async getInterviewQuestion(
    sessionId: string,
    studentId: string,
    role: string,
    level: string,
    skills: string[],
    previous?: PreviousTurnContext
  ): Promise<InterviewQuestionResponse> {
    const res = await fetch(`${API_BASE}/api/v1/interview/question`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        student_id: studentId,
        target_role: role,
        experience_level: level,
        current_skills: skills,
        ...previous,
      }),
    });
    if (!res.ok) {
      throw new Error(`Interview question error: ${res.statusText}`);
    }
    return res.json();
  },

  async transcribeAudio(file: Blob): Promise<{ transcript: string; domain_terms_detected?: string[] }> {
    const formData = new FormData();
    // Safari records MP4/AAC, Chrome and Firefox WebM/Opus; name the file after what was recorded
    const ext = file.type.includes("mp4") ? "m4a" : file.type.includes("ogg") ? "ogg" : "webm";
    formData.append("file", file, `answer.${ext}`);
    const res = await fetch(`${API_BASE}/api/v1/interview/transcribe`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      throw await apiError(res, "Audio transcription error");
    }
    return res.json();
  },

  /** Job roles covered by the interview question bank (for the role dropdown) */
  async getInterviewRoles(): Promise<RoleInfo[]> {
    const res = await fetch(`${API_BASE}/api/v1/interview/roles`);
    if (!res.ok) {
      throw await apiError(res, "Roles error");
    }
    return res.json();
  },

  /** Reads a CV (PDF, DOCX, TXT) on the server, in memory, and returns an interview profile */
  async analyzeCV(file: File): Promise<CVProfile> {
    const formData = new FormData();
    formData.append("file", file, file.name);
    const res = await fetch(`${API_BASE}/api/v1/interview/cv/analyze`, { method: "POST", body: formData });
    if (!res.ok) {
      throw await apiError(res, "CV analysis error");
    }
    return res.json();
  },

  /** Marks the interview completed and returns its report */
  async endInterview(sessionId: string): Promise<InterviewReport> {
    const res = await fetch(`${API_BASE}/api/v1/interview/${encodeURIComponent(sessionId)}/end`, { method: "POST" });
    if (!res.ok) {
      throw await apiError(res, "End interview error");
    }
    return res.json();
  },

  async getAvatarConfig(): Promise<AvatarConfig> {
    const res = await fetch(`${API_BASE}/api/v1/interview/avatar/config`);
    if (!res.ok) {
      throw await apiError(res, "Avatar config error");
    }
    return res.json();
  },

  async renderAvatarClip(text: string): Promise<{ job_ids: string[] }> {
    const res = await fetch(`${API_BASE}/api/v1/interview/avatar/render`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) {
      throw await apiError(res, "Avatar render error");
    }
    return res.json();
  },

  /** Drops clips that haven't started rendering (the candidate moved on) */
  async cancelAvatarClips(jobIds: string[]): Promise<void> {
    if (!jobIds.length) return;
    await fetch(`${API_BASE}/api/v1/interview/avatar/cancel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_ids: jobIds }),
    });
  },

  async getAvatarJob(jobId: string): Promise<AvatarJob> {
    const res = await fetch(`${API_BASE}/api/v1/interview/avatar/jobs/${encodeURIComponent(jobId)}`);
    if (!res.ok) {
      throw await apiError(res, "Avatar job error");
    }
    return res.json();
  },

  async getAvatarSessionToken(): Promise<AvatarSessionToken> {
    const res = await fetch(`${API_BASE}/api/v1/interview/avatar/token`, {
      method: "POST",
    });
    if (!res.ok) {
      throw new Error(`Avatar session token error: ${res.statusText}`);
    }
    return res.json();
  },

  async evaluateAnswer(
    turnId: string,
    transcript: string,
    studentId: string,
    telemetry?: DeliveryTelemetry
  ): Promise<EvaluationResponse> {
    const res = await fetch(`${API_BASE}/api/v1/interview/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        turn_id: turnId,
        transcript,
        student_id: studentId,
        ...telemetry,
      }),
    });
    if (!res.ok) {
      throw await apiError(res, "Interview evaluate error");
    }
    return res.json();
  },
};
