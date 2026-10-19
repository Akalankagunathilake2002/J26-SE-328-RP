// API client module for C03 Career Readiness Engine microservice

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export interface ReadinessHealthResponse {
  status: string;
  service: string;
}

export interface IndustryProfileItem {
  industry_profile_id: string;
  id?: string | null;
  role_id: string | null;
  role_name: string;
  career_level: string | null;
  domain_id: string | null;
  domain_name: string | null;
  domain: string | null;
  primary_observed_title: string | null;
  profile_version: string | null;
  profile_status: string | null;
}

export interface IndustryProfileQueryParams {
  domain_id?: string;
  career_level?: string;
  status?: string;
  latest_only?: boolean;
}

export interface AnalysisCreatePayload {
  user_id?: string;
  user_skill_profile_id?: string;
  role_id?: string;
  industry_profile_id?: string;
  matching_method?: string;
  scoring_config_version?: string;
  snapshot_id?: string;
}

export interface PrioritySkillItem {
  skillId: string;
  skillName: string;
  priorityRank: number;
  learningPriority: number;
  gap: number;
}

export interface C04AnalysisResponse {
  analysisId: string;
  user_id: string;
  roleId: string;
  roleName: string;
  readinessScore: number | null;
  baselineReadinessScore: number | null;
  prioritySkills: PrioritySkillItem[];
}

export interface SkillResultDetailItem {
  id: string;
  industry_requirement_id: string | null;
  required_skill_name: string;
  matched_skill_name: string | null;
  match_type: string;
  relationship_id: string | null;
  coverage_credit: number;
  required_proficiency: string;
  user_proficiency: string | null;
  evidence_confidence: number | null;
  industry_weight: number | null;
  satisfaction: number | null;
  gap: number | null;
  result_status: string;
}

export interface AnalysisDetailResponse {
  analysis_id: string;
  user_id: string;
  user_skill_profile_id: string;
  industry_profile_id: string;
  snapshot_id: string;
  role_id: string | null;
  role_name: string | null;
  career_level: string | null;
  matching_method: string;
  scoring_config_version: string;
  readiness_score: number | null;
  baseline_readiness_score: number | null;
  status: string;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  skill_results: SkillResultDetailItem[];
  priority_skills: PrioritySkillItem[];
  c04_payload?: Record<string, unknown> | null;
}

export interface AnalysisHistoryItem {
  analysis_id: string;
  analysisId: string;
  user_id: string;
  user_skill_profile_id: string;
  industry_profile_id: string;
  snapshot_id?: string | null;
  role_id: string;
  roleId: string;
  role_name: string | null;
  roleName: string | null;
  career_level: string | null;
  matching_method: string;
  scoring_config_version?: string | null;
  readiness_score: number | null;
  readinessScore: number | null;
  baseline_readiness_score: number | null;
  baselineReadinessScore: number | null;
  status: string;
  started_at: string;
  createdAt: string;
  completed_at: string | null;
  completedAt: string | null;
}

export interface AnalysisHistoryQueryParams {
  user_id?: string;
  status?: string;
  role_id?: string;
  limit?: number;
  offset?: number;
}

export interface AnalysisHistoryResponse {
  items: AnalysisHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface SkillExplanationItem {
  industryRequirementId?: string | null;
  skillName: string;
  matchedSkillName?: string | null;
  matchType: string;
  relationshipId?: string | null;
  coverageCredit: number;
  requiredProficiency: string;
  userProficiency?: string | null;
  evidenceConfidence?: number | null;
  industryWeight?: number | null;
  satisfaction?: number | null;
  gap?: number | null;
  resultStatus: string;
  readinessContribution?: number | null;
  maxPotentialContribution?: number | null;
  explanation: string;
  contributionExplanation: string;
}

export interface PriorityExplanationItem {
  skillId: string;
  skillName: string;
  priorityRank: number;
  learningPriority: number;
  gap: number;
  requiredProficiency: string;
  userProficiency?: string | null;
  demandWeight?: number | null;
  explanation: string;
}

export interface RelationshipExplanationItem {
  relationshipId: string;
  requiredSkillName: string;
  matchedSkillName: string;
  coverageCredit: number;
  explanation: string;
}

export interface ReadinessSummary {
  readinessScore: number;
  tier: string;
  interpretation: string;
  totalRequirements: number;
  assessableRequirements: number;
  satisfiedCount: number;
  partialCount: number;
  deficientCount: number;
  missingCount: number;
  unassessedCount: number;
  summaryText: string;
}

export interface AnalysisReportResponse {
  analysisId: string;
  user_id: string;
  roleId: string;
  roleName: string;
  status: string;
  startedAt: string;
  completedAt?: string | null;
  reportVersion: string;
  generatedAt: string;
  readinessSummary: ReadinessSummary;
  skillExplanations: SkillExplanationItem[];
  priorityExplanations: PriorityExplanationItem[];
  relationshipExplanations: RelationshipExplanationItem[];
}

export interface CandidateDiscoveryRun {
  id: string;
  analysis_id: string;
  embedding_model: string;
  similarity_threshold: number;
  status: string;
  candidates_submitted_count: number;
  started_at: string;
  completed_at?: string | null;
}

async function apiError(res: Response, label: string): Promise<Error> {
  try {
    const body = await res.json();
    if (body?.detail) {
      return new Error(typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail));
    }
  } catch {
    // Non-JSON error body fallback
  }
  return new Error(`${label}: ${res.statusText || res.status}`);
}

export const readinessApi = {
  // Check health and connectivity to the Readiness Engine
  async checkHealth(): Promise<ReadinessHealthResponse> {
    const res = await fetch(`${API_BASE}/readiness/health`);
    if (!res.ok) {
      throw await apiError(res, "Readiness health check failed");
    }
    return res.json();
  },

  // List available target industry profiles for role dropdown selection
  async getIndustryProfiles(params?: IndustryProfileQueryParams): Promise<IndustryProfileItem[]> {
    const query = new URLSearchParams();
    if (params?.domain_id) query.set("domain_id", params.domain_id);
    if (params?.career_level) query.set("career_level", params.career_level);
    if (params?.status) query.set("status", params.status);
    if (params?.latest_only !== undefined) query.set("latest_only", String(params.latest_only));

    const qs = query.toString();
    const url = `${API_BASE}/readiness/industry-profiles${qs ? `?${qs}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) {
      throw await apiError(res, "Failed to retrieve industry profiles");
    }
    return res.json();
  },

  // Retrieve a single industry profile by ID
  async getIndustryProfile(industryProfileId: string): Promise<IndustryProfileItem> {
    const res = await fetch(`${API_BASE}/readiness/industry-profiles/${encodeURIComponent(industryProfileId)}`);
    if (!res.ok) {
      throw await apiError(res, `Failed to retrieve industry profile ${industryProfileId}`);
    }
    return res.json();
  },

  // Trigger a new career readiness analysis run
  async createAnalysis(payload: AnalysisCreatePayload): Promise<C04AnalysisResponse> {
    const res = await fetch(`${API_BASE}/readiness/analyses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw await apiError(res, "Failed to initiate career readiness analysis");
    }
    return res.json();
  },

  // List paginated historical analysis records filtered by student user ID
  async listAnalyses(params?: AnalysisHistoryQueryParams): Promise<AnalysisHistoryResponse> {
    const query = new URLSearchParams();
    if (params?.user_id) query.set("user_id", params.user_id);
    if (params?.status) query.set("status", params.status);
    if (params?.role_id) query.set("role_id", params.role_id);
    if (params?.limit !== undefined) query.set("limit", String(params.limit));
    if (params?.offset !== undefined) query.set("offset", String(params.offset));

    const qs = query.toString();
    const url = `${API_BASE}/readiness/analyses${qs ? `?${qs}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) {
      throw await apiError(res, "Failed to retrieve analysis history");
    }
    return res.json();
  },

  // Retrieve detailed analysis execution results including per-skill breakdown
  async getAnalysisById(analysisId: string): Promise<AnalysisDetailResponse> {
    const res = await fetch(`${API_BASE}/readiness/analyses/${encodeURIComponent(analysisId)}`);
    if (!res.ok) {
      throw await apiError(res, `Failed to retrieve analysis details for ${analysisId}`);
    }
    return res.json();
  },

  // Retrieve C04-formatted output payload for downstream learning systems
  async getAnalysisC04(analysisId: string): Promise<C04AnalysisResponse> {
    const res = await fetch(`${API_BASE}/readiness/analyses/${encodeURIComponent(analysisId)}/c04`);
    if (!res.ok) {
      throw await apiError(res, `Failed to retrieve C04 payload for ${analysisId}`);
    }
    return res.json();
  },

  // Retrieve deterministic explanation report for modal narrative display
  async getAnalysisReport(analysisId: string): Promise<AnalysisReportResponse> {
    const res = await fetch(`${API_BASE}/readiness/analyses/${encodeURIComponent(analysisId)}/report`);
    if (!res.ok) {
      throw await apiError(res, `Failed to retrieve analysis explanation report for ${analysisId}`);
    }
    return res.json();
  },

  // Retrieve candidate discovery run audit records
  async getCandidateDiscoveryRuns(analysisId: string): Promise<CandidateDiscoveryRun[]> {
    const res = await fetch(`${API_BASE}/readiness/analyses/${encodeURIComponent(analysisId)}/candidate-discovery`);
    if (!res.ok) {
      throw await apiError(res, `Failed to retrieve candidate discovery runs for ${analysisId}`);
    }
    return res.json();
  },
};
