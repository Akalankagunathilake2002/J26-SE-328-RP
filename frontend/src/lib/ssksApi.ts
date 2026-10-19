// API client module for the Shared Skill Knowledge Service (SSKS) microservice

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export interface DomainItem {
  domain_id: string;
  name: string;
  code: string;
  description: string | null;
  status: string;
}

export interface RoleItem {
  role_id: string;
  preferred_name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SkillItem {
  skill_id: string;
  preferred_name: string;
  description: string | null;
  skill_type: string;
  skill_nature: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export type SkillRelationshipType =
  | "EQUIVALENT_TO"
  | "BROADER_THAN"
  | "NARROWER_THAN"
  | "PART_OF"
  | "PREREQUISITE_OF"
  | "RELATED_TO";

export interface SkillRelationshipItem {
  relationship_id: string;
  source_skill_id: string;
  target_skill_id: string;
  relationship_type: SkillRelationshipType;
  verification_status: string;
  source_id: string | null;
  evidence_note: string | null;
  created_at: string;
  updated_at: string;
}

export type CandidateReviewStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface CandidateRelationshipItem {
  candidate_relationship_id: string;
  source_skill_id: string;
  target_skill_id: string;
  proposed_relationship_type: SkillRelationshipType;
  confidence_score: number | null;
  review_status: CandidateReviewStatus;
  source_id: string | null;
  review_note: string | null;
  created_at: string;
  reviewed_at: string | null;
}

export interface ReviewCandidatePayload {
  action: "APPROVE" | "REJECT";
  review_note?: string;
}

export interface CreateDomainPayload {
  domain_id: string;
  name: string;
  code: string;
  description?: string;
  status?: string;
}

export interface CreateRolePayload {
  role_id: string;
  preferred_name: string;
  description?: string;
  status?: string;
}

export interface CreateSkillPayload {
  skill_id: string;
  preferred_name: string;
  description?: string;
  skill_type: string;
  skill_nature?: string;
  status?: string;
}

export interface CreateRelationshipPayload {
  source_skill_id: string;
  target_skill_id: string;
  relationship_type: SkillRelationshipType;
  verification_status?: string;
  source_id?: string;
  evidence_note?: string;
  relationship_id?: string;
}

async function handleApiError(res: Response, defaultMessage: string): Promise<never> {
  const body = await res.json().catch(() => null);
  const detail = body?.detail;
  if (typeof detail === "string") throw new Error(detail);
  if (Array.isArray(detail) && detail[0]?.msg) throw new Error(detail[0].msg);
  throw new Error(defaultMessage);
}

// Fetches all canonical domains from the SSKS service.
export async function fetchSsksDomains(): Promise<DomainItem[]> {
  const res = await fetch(`${API_BASE}/ssks/domains/`, { cache: "no-store" });
  if (!res.ok) {
    await handleApiError(res, `Failed to fetch domains (${res.status})`);
  }
  return res.json();
}

// Creates a new canonical domain in the SSKS knowledge base.
export async function createSsksDomain(payload: CreateDomainPayload): Promise<DomainItem> {
  const res = await fetch(`${API_BASE}/ssks/domains/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    await handleApiError(res, "Failed to create domain");
  }
  return res.json();
}

// Fetches canonical roles with optional filtering and pagination.
export async function fetchSsksRoles(params?: {
  limit?: number;
  offset?: number;
  status?: string;
  domain_id?: string;
}): Promise<RoleItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
  if (params?.status) searchParams.set("status", params.status);
  if (params?.domain_id) searchParams.set("domain_id", params.domain_id);

  const query = searchParams.toString();
  const url = `${API_BASE}/ssks/roles/${query ? `?${query}` : ""}`;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    await handleApiError(res, `Failed to fetch roles (${res.status})`);
  }
  return res.json();
}

// Creates a new canonical role in the SSKS knowledge base.
export async function createSsksRole(payload: CreateRolePayload): Promise<RoleItem> {
  const res = await fetch(`${API_BASE}/ssks/roles/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    await handleApiError(res, "Failed to create role");
  }
  return res.json();
}

// Fetches canonical skills with optional filtering and pagination.
export async function fetchSsksSkills(params?: {
  limit?: number;
  offset?: number;
  status?: string;
  skill_type?: string;
  skill_nature?: string;
  domain_id?: string;
}): Promise<SkillItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
  if (params?.status) searchParams.set("status", params.status);
  if (params?.skill_type) searchParams.set("skill_type", params.skill_type);
  if (params?.skill_nature) searchParams.set("skill_nature", params.skill_nature);
  if (params?.domain_id) searchParams.set("domain_id", params.domain_id);

  const query = searchParams.toString();
  const url = `${API_BASE}/ssks/skills/${query ? `?${query}` : ""}`;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    await handleApiError(res, `Failed to fetch skills (${res.status})`);
  }
  return res.json();
}

// Creates a new canonical skill in the SSKS knowledge base.
export async function createSsksSkill(payload: CreateSkillPayload): Promise<SkillItem> {
  const res = await fetch(`${API_BASE}/ssks/skills/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    await handleApiError(res, "Failed to create skill");
  }
  return res.json();
}

// Fetches verified skill relationships from the knowledge graph.
export async function fetchSsksRelationships(params?: {
  limit?: number;
  offset?: number;
  source_skill_id?: string;
  target_skill_id?: string;
  relationship_type?: string;
  verification_status?: string;
}): Promise<SkillRelationshipItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
  if (params?.source_skill_id) searchParams.set("source_skill_id", params.source_skill_id);
  if (params?.target_skill_id) searchParams.set("target_skill_id", params.target_skill_id);
  if (params?.relationship_type) searchParams.set("relationship_type", params.relationship_type);
  if (params?.verification_status) searchParams.set("verification_status", params.verification_status);

  const query = searchParams.toString();
  const url = `${API_BASE}/ssks/relationships${query ? `?${query}` : ""}`;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    await handleApiError(res, `Failed to fetch relationships (${res.status})`);
  }
  return res.json();
}

// Creates a new verified skill relationship in the SSKS knowledge graph.
export async function createSsksRelationship(
  payload: CreateRelationshipPayload,
): Promise<SkillRelationshipItem> {
  const res = await fetch(`${API_BASE}/ssks/relationships`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    await handleApiError(res, "Failed to create relationship");
  }
  return res.json();
}

// Fetches candidate relationships proposed for verification.
export async function fetchSsksCandidateRelationships(params?: {
  limit?: number;
  offset?: number;
  source_skill_id?: string;
  target_skill_id?: string;
  relationship_type?: string;
  review_status?: string;
}): Promise<CandidateRelationshipItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
  if (params?.source_skill_id) searchParams.set("source_skill_id", params.source_skill_id);
  if (params?.target_skill_id) searchParams.set("target_skill_id", params.target_skill_id);
  if (params?.relationship_type) searchParams.set("relationship_type", params.relationship_type);
  if (params?.review_status) searchParams.set("review_status", params.review_status);

  const query = searchParams.toString();
  const url = `${API_BASE}/ssks/candidates/relationships${query ? `?${query}` : ""}`;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    await handleApiError(res, `Failed to fetch candidate relationships (${res.status})`);
  }
  return res.json();
}

// Submits a review action (approve or reject) for a proposed candidate relationship.
export async function reviewCandidateRelationship(
  candidateRelationshipId: string,
  payload: ReviewCandidatePayload,
  reviewerId: string = "admin-reviewer",
): Promise<CandidateRelationshipItem> {
  const url = `${API_BASE}/ssks/candidates/relationships/${candidateRelationshipId}/review`;

  const res = await fetch(url, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-Reviewer-Id": reviewerId,
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    await handleApiError(res, `Failed to review candidate relationship (${res.status})`);
  }

  return res.json();
}
