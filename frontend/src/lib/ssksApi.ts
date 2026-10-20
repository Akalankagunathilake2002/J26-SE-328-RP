// API client module for the Shared Skill Knowledge Service (SSKS) microservice

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window === "undefined" ? process.env.API_GATEWAY_URL : undefined) ||
  "http://localhost:8080";

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
  domain_id?: string;
  name: string;
  code: string;
  description?: string;
  status?: string;
}

export interface CreateRolePayload {
  role_id?: string;
  preferred_name: string;
  description?: string;
  status?: string;
  domain_id?: string;
}

export interface CreateSkillPayload {
  skill_id?: string;
  preferred_name: string;
  description?: string;
  skill_type: string;
  skill_nature?: string;
  status?: string;
  domain_id?: string;
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

// Safe wrapper around fetch providing meaningful diagnostic context if the network request fails.
async function safeFetch(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    throw new Error(
      `Network connection error: Failed to reach backend at ${url} (${errorMsg}). Please check that the API gateway is running on ${API_BASE}.`,
    );
  }
}

// Extracts meaningful HTTP error details from failed backend API responses.
async function handleApiError(res: Response, defaultMessage: string): Promise<never> {
  let errorDetail = "";
  try {
    const text = await res.text();
    try {
      const body = JSON.parse(text);
      if (typeof body?.detail === "string") {
        errorDetail = body.detail;
      } else if (Array.isArray(body?.detail)) {
        errorDetail = body.detail
          .map((item: { loc?: (string | number)[]; msg?: string }) => {
            const field = item.loc && item.loc.length > 1 ? item.loc.slice(1).join(".") : "";
            return field ? `${field}: ${item.msg}` : (item.msg || "Invalid field");
          })
          .join("; ");
      } else if (body?.message) {
        errorDetail = String(body.message);
      }
    } catch {
      if (text && text.trim().length > 0 && text.length < 300) {
        errorDetail = text.trim();
      }
    }
  } catch {
    // Ignore body read errors
  }

  const statusText = res.statusText ? ` ${res.statusText}` : "";
  const suffix = `(HTTP ${res.status}${statusText})`;
  const finalMessage = errorDetail ? `${errorDetail} ${suffix}` : `${defaultMessage} ${suffix}`;
  throw new Error(finalMessage);
}

// Fetches all canonical domains from the SSKS service.
export async function fetchSsksDomains(): Promise<DomainItem[]> {
  const res = await safeFetch(`${API_BASE}/ssks/domains/`, { cache: "no-store" });
  if (!res.ok) {
    await handleApiError(res, `Failed to fetch domains (${res.status})`);
  }
  return res.json();
}

// Creates a new canonical domain in the SSKS knowledge base.
export async function createSsksDomain(payload: CreateDomainPayload): Promise<DomainItem> {
  const { domain_id, ...domainData } = payload;
  const bodyData = domain_id && domain_id.trim() ? { ...domainData, domain_id: domain_id.trim() } : domainData;
  const res = await safeFetch(`${API_BASE}/ssks/domains/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyData),
  });
  if (!res.ok) {
    await handleApiError(res, "Failed to create domain");
  }
  return res.json();
}

// Associates a canonical skill with a domain.
export async function associateSkillDomain(
  skillId: string,
  domainId: string,
): Promise<{ skill_id: string; domain_id: string }> {
  const res = await safeFetch(`${API_BASE}/ssks/skills/${skillId}/domains/${domainId}`, {
    method: "PUT",
  });
  if (!res.ok) {
    await handleApiError(res, `Failed to associate skill with domain (${res.status})`);
  }
  return res.json();
}

// Associates a canonical role with a domain.
export async function associateRoleDomain(
  roleId: string,
  domainId: string,
): Promise<{ role_id: string; domain_id: string }> {
  const res = await safeFetch(`${API_BASE}/ssks/roles/${roleId}/domains/${domainId}`, {
    method: "PUT",
  });
  if (!res.ok) {
    await handleApiError(res, `Failed to associate role with domain (${res.status})`);
  }
  return res.json();
}

// Fetches canonical roles with optional filtering, search, and pagination.
export async function fetchSsksRoles(params?: {
  limit?: number;
  offset?: number;
  status?: string;
  domain_id?: string;
  search?: string;
}): Promise<RoleItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
  if (params?.status) searchParams.set("status", params.status);
  if (params?.domain_id) searchParams.set("domain_id", params.domain_id);
  if (params?.search) searchParams.set("search", params.search);

  const query = searchParams.toString();
  const url = `${API_BASE}/ssks/roles/${query ? `?${query}` : ""}`;

  const res = await safeFetch(url, { cache: "no-store" });
  if (!res.ok) {
    await handleApiError(res, `Failed to fetch roles (${res.status})`);
  }
  return res.json();
}

// Retrieves all roles by paginating through all available pages.
export async function fetchSsksRolesAll(params?: {
  status?: string;
  domain_id?: string;
  search?: string;
}): Promise<RoleItem[]> {
  const allRoles: RoleItem[] = [];
  const pageSize = 500;
  let offset = 0;

  while (true) {
    const batch = await fetchSsksRoles({
      ...params,
      limit: pageSize,
      offset,
    });
    allRoles.push(...batch);
    if (batch.length < pageSize) {
      break;
    }
    offset += pageSize;
  }

  return allRoles;
}

// Creates a new canonical role, with optional automatic domain linking.
export async function createSsksRole(payload: CreateRolePayload): Promise<RoleItem> {
  const { domain_id, role_id, ...roleData } = payload;
  const bodyData = role_id && role_id.trim() ? { ...roleData, role_id: role_id.trim() } : roleData;
  const res = await safeFetch(`${API_BASE}/ssks/roles/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyData),
  });
  if (!res.ok) {
    await handleApiError(res, "Failed to create role");
  }
  const createdRole: RoleItem = await res.json();

  if (domain_id && createdRole.role_id) {
    try {
      await associateRoleDomain(createdRole.role_id, domain_id);
    } catch (assocErr) {
      console.warn("Failed to associate domain to role:", assocErr);
    }
  }

  return createdRole;
}

// Fetches canonical skills with optional filtering, search, and pagination.
export async function fetchSsksSkills(params?: {
  limit?: number;
  offset?: number;
  status?: string;
  skill_type?: string;
  skill_nature?: string;
  domain_id?: string;
  search?: string;
}): Promise<SkillItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
  if (params?.status) searchParams.set("status", params.status);
  if (params?.skill_type) searchParams.set("skill_type", params.skill_type);
  if (params?.skill_nature) searchParams.set("skill_nature", params.skill_nature);
  if (params?.domain_id) searchParams.set("domain_id", params.domain_id);
  if (params?.search) searchParams.set("search", params.search);

  const query = searchParams.toString();
  const url = `${API_BASE}/ssks/skills/${query ? `?${query}` : ""}`;

  const res = await safeFetch(url, { cache: "no-store" });
  if (!res.ok) {
    await handleApiError(res, `Failed to fetch skills (${res.status})`);
  }
  return res.json();
}

// Retrieves all skills by paginating in chunks of 500 records.
export async function fetchSsksSkillsAll(params?: {
  status?: string;
  skill_type?: string;
  skill_nature?: string;
  domain_id?: string;
  search?: string;
}): Promise<SkillItem[]> {
  const allSkills: SkillItem[] = [];
  const pageSize = 500;
  let offset = 0;

  while (true) {
    const batch = await fetchSsksSkills({
      ...params,
      limit: pageSize,
      offset,
    });
    allSkills.push(...batch);
    if (batch.length < pageSize) {
      break;
    }
    offset += pageSize;
  }

  return allSkills;
}

// Creates a new canonical skill, with optional automatic domain linking.
export async function createSsksSkill(payload: CreateSkillPayload): Promise<SkillItem> {
  const { domain_id, skill_id, ...skillData } = payload;
  const bodyData = skill_id && skill_id.trim() ? { ...skillData, skill_id: skill_id.trim() } : skillData;
  const res = await safeFetch(`${API_BASE}/ssks/skills/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyData),
  });
  if (!res.ok) {
    await handleApiError(res, "Failed to create skill");
  }
  const createdSkill: SkillItem = await res.json();

  if (domain_id && createdSkill.skill_id) {
    try {
      await associateSkillDomain(createdSkill.skill_id, domain_id);
    } catch (assocErr) {
      console.warn("Failed to associate domain to skill:", assocErr);
    }
  }

  return createdSkill;
}

// Fetches verified skill relationships from the knowledge graph.
export async function fetchSsksRelationships(params?: {
  limit?: number;
  offset?: number;
  source_skill_id?: string;
  target_skill_id?: string;
  relationship_type?: string;
  verification_status?: string;
  search?: string;
}): Promise<SkillRelationshipItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
  if (params?.source_skill_id) searchParams.set("source_skill_id", params.source_skill_id);
  if (params?.target_skill_id) searchParams.set("target_skill_id", params.target_skill_id);
  if (params?.relationship_type) searchParams.set("relationship_type", params.relationship_type);
  if (params?.verification_status) searchParams.set("verification_status", params.verification_status);
  if (params?.search) searchParams.set("search", params.search);

  const query = searchParams.toString();
  const url = `${API_BASE}/ssks/relationships${query ? `?${query}` : ""}`;

  const res = await safeFetch(url, { cache: "no-store" });
  if (!res.ok) {
    await handleApiError(res, `Failed to fetch relationships (${res.status})`);
  }
  return res.json();
}

// Retrieves all verified relationships by paginating in chunks of 500 records.
export async function fetchSsksRelationshipsAll(params?: {
  source_skill_id?: string;
  target_skill_id?: string;
  relationship_type?: string;
  verification_status?: string;
  search?: string;
}): Promise<SkillRelationshipItem[]> {
  const allRels: SkillRelationshipItem[] = [];
  const pageSize = 500;
  let offset = 0;

  while (true) {
    const batch = await fetchSsksRelationships({
      ...params,
      limit: pageSize,
      offset,
    });
    allRels.push(...batch);
    if (batch.length < pageSize) {
      break;
    }
    offset += pageSize;
  }

  return allRels;
}

// Creates a new verified skill relationship in the SSKS knowledge graph.
export async function createSsksRelationship(
  payload: CreateRelationshipPayload,
): Promise<SkillRelationshipItem> {
  const { relationship_id, ...relData } = payload;
  const bodyData =
    relationship_id && relationship_id.trim()
      ? { ...relData, relationship_id: relationship_id.trim() }
      : relData;
  const res = await safeFetch(`${API_BASE}/ssks/relationships`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyData),
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

  const res = await safeFetch(url, { cache: "no-store" });
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
  const cleanId = encodeURIComponent(candidateRelationshipId.trim());
  const effectiveReviewerId = reviewerId && reviewerId.trim() ? reviewerId.trim() : "admin-reviewer";
  const url = `${API_BASE}/ssks/candidates/relationships/${cleanId}/review`;

  const res = await safeFetch(url, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-Reviewer-Id": effectiveReviewerId,
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    await handleApiError(res, `Failed to review candidate relationship (${res.status})`);
  }

  return res.json();
}
