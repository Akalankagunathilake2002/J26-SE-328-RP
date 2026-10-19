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

// Formatted role option for the target role selector
export interface TargetRoleOption {
  id: string;
  roleId: string;
  label: string;
  roleName: string;
  careerLevel: string;
  domainName: string;
}

// Summary overview metrics derived from analysis history
export interface OverviewMetrics {
  overallReadiness: number;
  readinessTrend: string;
  analysesCompleted: number;
  analysesTrend: string;
  topMatchingRole: string;
  matchPercentage: number;
  rolesExplored: number;
  rolesTrend: string;
}

// Single skill result item formatted for the results modal
export interface ReadinessSkillResult {
  id: string;
  requiredSkillName: string;
  matchedSkillName?: string;
  matchType: string;
  relationshipId?: string;
  coverageCredit: number;
  requiredProficiency: string;
  userProficiency?: string;
  gap?: number;
  resultStatus: string;
  explanation?: string;
  evidenceConfidence?: number;
  satisfaction?: number;
  industryWeight?: number;
  readinessContribution?: number;
  maxPotentialContribution?: number;
}

// Actionable priority gap item conforming to C04 contract
export interface ReadinessPrioritySkill {
  skillId: string;
  skillName: string;
  priorityRank: number;
  learningPriority: number;
  gap: number;
  requiredProficiency?: string;
  explanation?: string;
}

// Full analysis evaluation details consumed by the results modal
export interface DetailedAnalysisResult {
  analysisId: string;
  roleId: string;
  roleName: string;
  careerLevel: string;
  readinessScore: number;
  baselineReadinessScore?: number;
  tier: string;
  explanation: string;
  totalRequirements: number;
  satisfiedCount: number;
  partialCount: number;
  missingCount: number;
  matchedCount?: number;
  skills: ReadinessSkillResult[];
  prioritySkills: ReadinessPrioritySkill[];
}

// Formats career level strings into human-readable titles
export function formatCareerLevel(level?: string | null): string {
  if (!level) return "Junior";
  const normalized = level.trim().toUpperCase();
  switch (normalized) {
    case "INTERNSHIP":
    case "INTERN":
      return "Internship";
    case "JUNIOR":
    case "ENTRY_LEVEL":
      return "Junior";
    case "MID":
    case "MID_LEVEL":
      return "Mid-Level";
    case "SENIOR":
      return "Senior";
    case "LEAD":
      return "Lead";
    default:
      return level.charAt(0).toUpperCase() + level.slice(1).toLowerCase();
  }
}

// Formats ISO date timestamps for table display
export function formatAnalysisDate(dateString?: string | null): string {
  if (!dateString) return "Recently";
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return "Recently";
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(d);
  } catch {
    return "Recently";
  }
}

// Derives overview cards metrics from real analysis history records
export function deriveOverviewStats(
  items: AnalysisHistoryItem[] = [],
  totalCount = 0,
): OverviewMetrics {
  const completed = items.filter(
    (a) => a.status === "COMPLETED" && (a.readinessScore !== null || a.readiness_score !== null),
  );

  if (completed.length === 0) {
    return {
      overallReadiness: 0,
      readinessTrend: "No analyses yet",
      analysesCompleted: totalCount || items.length,
      analysesTrend: totalCount === 0 ? "Start your first analysis" : `${totalCount} total initiated`,
      topMatchingRole: "No roles\nevaluated",
      matchPercentage: 0,
      rolesExplored: 0,
      rolesTrend: "Information Technology — IT",
    };
  }

  const scores = completed.map((a) => Number(a.readinessScore ?? a.readiness_score ?? 0));
  const avgScore = Math.round(scores.reduce((sum, s) => sum + s, 0) / scores.length);

  let readinessTrend = "Average across evaluations";
  if (completed.length >= 2) {
    const latest = scores[0];
    const prev = scores[1];
    const diff = latest - prev;
    if (diff > 0) {
      readinessTrend = `+${Math.round(diff)}% vs previous`;
    } else if (diff < 0) {
      readinessTrend = `${Math.round(diff)}% vs previous`;
    } else {
      readinessTrend = "Same as previous";
    }
  } else {
    readinessTrend = `Latest: ${scores[0]}%`;
  }

  let topRole = completed[0];
  let maxScore = Number(topRole.readinessScore ?? topRole.readiness_score ?? 0);
  for (const item of completed) {
    const s = Number(item.readinessScore ?? item.readiness_score ?? 0);
    if (s > maxScore) {
      maxScore = s;
      topRole = item;
    }
  }

  const rawRoleName = topRole.role_name || topRole.roleName || "Target Role";
  const topRoleDisplay = rawRoleName.includes("—")
    ? rawRoleName.split("—")[0].trim()
    : rawRoleName;

  const distinctRoles = new Set(
    items.map((a) => a.industry_profile_id || a.role_id || a.roleId),
  ).size;

  return {
    overallReadiness: avgScore,
    readinessTrend,
    analysesCompleted: totalCount || items.length,
    analysesTrend: totalCount > items.length ? `Showing ${items.length} of ${totalCount}` : `${completed.length} completed`,
    topMatchingRole: topRoleDisplay,
    matchPercentage: Math.round(maxScore),
    rolesExplored: distinctRoles,
    rolesTrend: "Information Technology — IT",
  };
}

// Combines analysis detail and report endpoints into a unified modal result
export async function fetchDetailedAnalysisResult(analysisId: string): Promise<DetailedAnalysisResult> {
  const detail = await readinessApi.getAnalysisById(analysisId);

  let report: AnalysisReportResponse | null = null;
  try {
    report = await readinessApi.getAnalysisReport(analysisId);
  } catch {
    report = null;
  }

  const rawScore = report?.readinessSummary?.readinessScore ?? detail.readiness_score ?? 0;
  const score = Math.round(Number(rawScore) || 0);

  const tier =
    report?.readinessSummary?.tier ||
    (score >= 80 ? "Excellent Readiness" : score >= 60 ? "Good Readiness" : "Moderate Readiness");

  const skills: ReadinessSkillResult[] = (detail.skill_results || []).map((sr) => {
    const exp = report?.skillExplanations?.find(
      (e) => (e.industryRequirementId && e.industryRequirementId === sr.industry_requirement_id) || e.skillName === sr.required_skill_name,
    );
    return {
      id: sr.id || sr.industry_requirement_id || sr.required_skill_name,
      requiredSkillName: sr.required_skill_name,
      matchedSkillName: sr.matched_skill_name || undefined,
      matchType: sr.match_type || "MISSING",
      relationshipId: sr.relationship_id || undefined,
      coverageCredit: sr.coverage_credit ?? 0,
      requiredProficiency: sr.required_proficiency || "INTERMEDIATE",
      userProficiency: sr.user_proficiency || undefined,
      gap: sr.gap ?? undefined,
      resultStatus: sr.result_status || "MISSING",
      explanation: exp?.explanation || exp?.contributionExplanation,
      evidenceConfidence: sr.evidence_confidence ?? exp?.evidenceConfidence ?? undefined,
      satisfaction: sr.satisfaction ?? exp?.satisfaction ?? undefined,
      industryWeight: sr.industry_weight ?? exp?.industryWeight ?? undefined,
      readinessContribution: exp?.readinessContribution ?? undefined,
      maxPotentialContribution: exp?.maxPotentialContribution ?? undefined,
    };
  });

  if (skills.length === 0 && report?.skillExplanations) {
    for (const exp of report.skillExplanations) {
      skills.push({
        id: exp.industryRequirementId || exp.skillName,
        requiredSkillName: exp.skillName,
        matchedSkillName: exp.matchedSkillName || undefined,
        matchType: exp.matchType || "MISSING",
        relationshipId: exp.relationshipId || undefined,
        coverageCredit: exp.coverageCredit ?? 0,
        requiredProficiency: exp.requiredProficiency || "INTERMEDIATE",
        userProficiency: exp.userProficiency || undefined,
        gap: exp.gap ?? undefined,
        resultStatus: exp.resultStatus || "MISSING",
        explanation: exp.explanation || exp.contributionExplanation,
        evidenceConfidence: exp.evidenceConfidence ?? undefined,
        satisfaction: exp.satisfaction ?? undefined,
        industryWeight: exp.industryWeight ?? undefined,
        readinessContribution: exp.readinessContribution ?? undefined,
        maxPotentialContribution: exp.maxPotentialContribution ?? undefined,
      });
    }
  }

  const totalRequirements =
    report?.readinessSummary?.totalRequirements ?? detail.skill_results?.length ?? skills.length;

  // Fully satisfied count: requirements where satisfaction achieves 100% (>= 0.999)
  // Does NOT treat COVERED skills as fully satisfied if satisfaction is below 1
  const satisfiedCount =
    report?.readinessSummary?.satisfiedCount ??
    detail.skill_results?.filter((s) => (s.satisfaction !== null && s.satisfaction !== undefined ? s.satisfaction >= 0.999 : s.result_status === "SATISFIED")).length ??
    skills.filter((s) => (s.satisfaction !== undefined ? s.satisfaction >= 0.999 : s.resultStatus === "SATISFIED")).length;

  // Partial count: requirements with satisfaction between 0 and 1, including covered skills with evidence confidence < 1
  const partialCount =
    report?.readinessSummary?.partialCount ??
    detail.skill_results?.filter((s) => (s.satisfaction !== null && s.satisfaction !== undefined ? s.satisfaction > 0 && s.satisfaction < 0.999 : s.result_status === "PARTIAL" || s.result_status === "PARTIALLY_COVERED")).length ??
    skills.filter((s) => (s.satisfaction !== undefined ? s.satisfaction > 0 && s.satisfaction < 0.999 : s.resultStatus === "PARTIAL" || s.resultStatus === "PARTIALLY_COVERED")).length;

  const missingCount =
    (report?.readinessSummary?.missingCount ?? 0) + (report?.readinessSummary?.deficientCount ?? 0) ||
    detail.skill_results?.filter((s) => s.result_status === "MISSING" || s.result_status === "DEFICIENT" || s.match_type === "MISSING").length ||
    skills.filter((s) => s.resultStatus === "MISSING" || s.resultStatus === "DEFICIENT" || s.matchType === "MISSING").length;

  // Matched count: requirements where candidate has a demonstrated matching skill
  const matchedCount =
    detail.skill_results?.filter((s) => s.match_type !== "MISSING" && s.match_type !== "UNASSESSED" && (s.coverage_credit > 0 || s.result_status !== "MISSING")).length ??
    skills.filter((s) => s.matchType !== "MISSING" && s.matchType !== "UNASSESSED" && (s.coverageCredit > 0 || s.resultStatus !== "MISSING")).length;

  let explanation =
    report?.readinessSummary?.summaryText ||
    report?.readinessSummary?.interpretation ||
    detail.error_message ||
    "";

  if (!explanation) {
    if (matchedCount === totalRequirements && totalRequirements > 0 && satisfiedCount === 0) {
      explanation = `All ${totalRequirements} skills match your profile with zero capability gaps. Your readiness score of ${score}% reflects developing evidence confidence rather than missing skills. Verifying skills with certificates or assessments will increase your score.`;
    } else {
      explanation = `Evaluated ${totalRequirements} requirement(s) for role '${detail.role_name || "Target Role"}'. ${satisfiedCount} fully satisfied, ${partialCount} partial, and ${missingCount} missing.`;
    }
  }

  const prioritySkills: ReadinessPrioritySkill[] = (detail.priority_skills || []).map((ps) => {
    const prioExp = report?.priorityExplanations?.find((pe) => pe.skillId === ps.skillId);
    return {
      skillId: ps.skillId,
      skillName: ps.skillName,
      priorityRank: ps.priorityRank,
      learningPriority: ps.learningPriority,
      gap: ps.gap,
      requiredProficiency: prioExp?.requiredProficiency,
      explanation: prioExp?.explanation,
    };
  });

  if (prioritySkills.length === 0 && report?.priorityExplanations) {
    for (const pe of report.priorityExplanations) {
      prioritySkills.push({
        skillId: pe.skillId,
        skillName: pe.skillName,
        priorityRank: pe.priorityRank,
        learningPriority: pe.learningPriority,
        gap: pe.gap,
        requiredProficiency: pe.requiredProficiency,
        explanation: pe.explanation,
      });
    }
  }

  return {
    analysisId: detail.analysis_id || analysisId,
    roleId: detail.role_id || detail.industry_profile_id || "",
    roleName: detail.role_name || report?.roleName || "Target Role",
    careerLevel: detail.career_level || "Junior",
    readinessScore: score,
    baselineReadinessScore:
      detail.baseline_readiness_score !== null && detail.baseline_readiness_score !== undefined
        ? Math.round(Number(detail.baseline_readiness_score))
        : undefined,
    tier,
    explanation,
    totalRequirements,
    satisfiedCount,
    partialCount,
    missingCount,
    skills,
    prioritySkills,
  };
}
