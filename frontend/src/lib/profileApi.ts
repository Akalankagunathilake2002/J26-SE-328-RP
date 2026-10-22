// API client for the C02 Evidence-Based Skill Profile microservice.
// Requests go through the API gateway; set NEXT_PUBLIC_PROFILE_API_URL to call the service directly
// (for example http://localhost:8004 while running it outside Docker).

const API_BASE =
  process.env.NEXT_PUBLIC_PROFILE_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export type SourceType =
  | "cv"
  | "project_description"
  | "academic_document"
  | "certificate"
  | "portfolio_link";

export type EvidenceType =
  | "project_demonstrated"
  | "cv_self_reported"
  | "academic_exposure"
  | "certificate_supported"
  | "portfolio_supported"
  | "unverified_mention";

export type ConfidenceLevel = "strong" | "moderate" | "weak";

export interface ProfileDocument {
  name: string;
  source_type: SourceType;
  type_detected_by: string | null;
  type_confidence: number | null;
  sections: string[];
  skill_count: number;
}

export interface EvidenceContribution {
  source: SourceType;
  evidence_type: EvidenceType;
  mentions: number;
  strength: number;
}

export interface SkillMention {
  skill_id: string;
  name: string;
  matched_text: string;
  section: string;
  sentence: string;
  method: string;
  match_method: string;
  match_score: number;
  evidence_type: EvidenceType;
}

export interface ProfileSkill {
  skill_id: string;
  name: string;
  confidence: number;
  confidence_level: ConfidenceLevel;
  evidence: EvidenceContribution[];
  documents: string[];
  source_types: SourceType[];
  mentions: SkillMention[];
}

export interface UnlinkedSpan {
  text: string;
  section: string;
  sentence: string;
  detection_score: number;
}

export interface SkillProfile {
  documents: ProfileDocument[];
  skills: ProfileSkill[];
  unlinked: UnlinkedSpan[];
  /** When the profile was saved for the user (null when it could not be saved). */
  saved_at: string | null;
}

export const SOURCE_LABELS: Record<SourceType, string> = {
  cv: "CV",
  project_description: "Project report",
  academic_document: "Academic document",
  certificate: "Certificate",
  portfolio_link: "GitHub",
};

export const EVIDENCE_LABELS: Record<EvidenceType, string> = {
  project_demonstrated: "used in work",
  cv_self_reported: "listed",
  academic_exposure: "studied",
  certificate_supported: "certified",
  portfolio_supported: "in code",
  unverified_mention: "interest only",
};

async function errorMessage(response: Response): Promise<string> {
  const body = await response.json().catch(() => null);
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (response.status >= 502) return "The skill profile service is not running. Please try again shortly.";
  return `Request failed (${response.status})`;
}

export const profileApi = {
  /** Build one profile from documents and GitHub links and save it for the user. */
  async buildProfile(files: File[], githubLinks: string[], userId: string): Promise<SkillProfile> {
    const form = new FormData();
    form.append("user_id", userId);
    files.forEach((file) => form.append("files", file));
    githubLinks.filter((link) => link.trim()).forEach((link) => form.append("portfolio_links", link.trim()));

    let response: Response;
    try {
      response = await fetch(`${API_BASE}/api/v1/profile/build`, { method: "POST", body: form });
    } catch {
      throw new Error("Can't reach the skill profile service. Is it running?");
    }
    if (!response.ok) throw new Error(await errorMessage(response));
    return response.json();
  },

  /** The user's last saved profile, or null when they have not built one yet. */
  async getSavedProfile(userId: string): Promise<SkillProfile | null> {
    let response: Response;
    try {
      response = await fetch(`${API_BASE}/api/v1/profile/users/${encodeURIComponent(userId)}`);
    } catch {
      throw new Error("Can't reach the skill profile service. Is it running?");
    }
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(await errorMessage(response));
    return response.json();
  },

  /** Delete the user's saved profile, so they can build a new one from scratch. */
  async clearProfile(userId: string): Promise<void> {
    let response: Response;
    try {
      response = await fetch(`${API_BASE}/api/v1/profile/users/${encodeURIComponent(userId)}`, {
        method: "DELETE",
      });
    } catch {
      throw new Error("Can't reach the skill profile service. Is it running?");
    }
    if (!response.ok) throw new Error(await errorMessage(response));
  },
};
