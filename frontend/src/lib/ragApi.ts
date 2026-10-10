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
  content_preview: string;
  similarity_score: number;
  source: string;
  topic: string;
  dense_rank?: number;
  sparse_rank?: number;
  rrf_score?: number;
  retrieval_method?: string;
}

export interface LearningResponse {
  answer: string;
  recommended_next_topic: string;
  sources: SourceCitation[];
  retrieved_chunks: RetrievedChunk[];
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  total_latency_ms: number;
  retrieval_strategy?: string;
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
  evaluation_latency_ms: number;
}

export const ragApi = {
  async askLearning(payload: LearningQueryPayload): Promise<LearningResponse> {
    const res = await fetch(`${API_BASE}/api/v1/learning/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(`Learning API error: ${res.statusText}`);
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
    skills: string[]
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
      }),
    });
    if (!res.ok) {
      throw new Error(`Interview question error: ${res.statusText}`);
    }
    return res.json();
  },

  async transcribeAudio(file: Blob): Promise<{ transcript: string }> {
    const formData = new FormData();
    formData.append("file", file, "answer.webm");
    const res = await fetch(`${API_BASE}/api/v1/interview/transcribe`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      throw new Error(`Audio transcription error: ${res.statusText}`);
    }
    return res.json();
  },

  async evaluateAnswer(turnId: string, transcript: string, studentId: string): Promise<EvaluationResponse> {
    const res = await fetch(`${API_BASE}/api/v1/interview/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        turn_id: turnId,
        transcript,
        student_id: studentId,
      }),
    });
    if (!res.ok) {
      throw new Error(`Interview evaluate error: ${res.statusText}`);
    }
    return res.json();
  },
};
