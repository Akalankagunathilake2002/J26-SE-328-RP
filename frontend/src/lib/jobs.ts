import "server-only";

import { cookies } from "next/headers";

import { SESSION_COOKIE } from "@/lib/auth";

// Company job posts, from the job-market-intelligence-engine service (C01) through the API gateway.
// Companies post jobs, an admin verifies each company, students apply on Skillaro. Only the Next.js server
// calls the service, with the logged-in user's token from the session cookie.
const API_GATEWAY_URL = process.env.API_GATEWAY_URL ?? "http://localhost:8080";

export type CompanyStatus = "PENDING" | "VERIFIED" | "REJECTED";
export type JobStatus = "DRAFT" | "PUBLISHED" | "CLOSED";
/** What a job is right now: WAITING = published, company not verified yet; HIDDEN = company rejected. */
export type JobState = "DRAFT" | "WAITING" | "HIDDEN" | "LIVE" | "EXPIRED" | "CLOSED";
export type ApplicationStatus = "NEW" | "SEEN" | "SHORTLISTED" | "NOT_SELECTED";
export type Importance = "REQUIRED" | "PREFERRED";
export type SkillType = "TECHNICAL" | "BEHAVIOURAL";

export type Company = {
  company_id: string;
  name: string;
  website: string | null;
  sector: string | null;
  city: string | null;
  description: string | null;
  contact_name: string | null;
  contact_email: string | null;
  status: CompanyStatus;
  created_at: string;
  verified_at: string | null;
  rejected_at: string | null;
  published?: number | null;
  drafts?: number | null;
  applicants?: number | null;
  new_applicants?: number | null;
};

export type JobSkill = { name: string; skill_type: SkillType; importance: Importance; skill_id?: string | null };

export type Job = {
  vacancy_id: string;
  title: string;
  career_level: string | null;
  employment_type: string | null;
  location: string | null;
  description: string;
  closing_date: string | null;
  apply_url: string | null;
  status: JobStatus;
  state: JobState;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  company: { company_id: string; name: string; sector: string | null; city: string | null; website: string | null };
  required: string[];
  preferred: string[];
  skills: JobSkill[];
  education: string | null;
  minimum_years: number | null;
  certifications: string[];
  applicants?: number | null;
  new_applicants?: number | null;
  application_status?: ApplicationStatus | null;
};

export type JobInput = {
  title: string;
  career_level: string;
  employment_type: string;
  location: string | null;
  closing_date: string | null;
  apply_url: string | null;
  description: string;
  status: "DRAFT" | "PUBLISHED";
  skills: { name: string; importance: Importance; skill_type?: SkillType }[];
  education: string | null;
  minimum_years: number | null;
  certifications: string[];
};

export type DetectedSkills = {
  skills: { name: string; skill_type: SkillType; category: string; importance: Importance; in_skill_list: boolean }[];
  education: string | null;
  minimum_years: number | null;
  certifications: string[];
};

export type Applicant = {
  application_id: string;
  vacancy_id: string;
  job_title: string;
  full_name: string;
  email: string;
  phone: string;
  education: string | null;
  note: string | null;
  status: ApplicationStatus;
  applied_at: string;
  updated_at: string;
  cv_file_name: string | null;
  cv_size_bytes: number | null;
};

export type MyApplication = {
  application_id: string;
  vacancy_id: string;
  status: ApplicationStatus;
  applied_at: string;
  title: string;
  location: string | null;
  company_id: string;
  company_name: string;
  job_open: boolean;
  cv_file_name: string | null;
};

export type MyApplications = {
  applications: MyApplication[];
  last_cv: { file_name: string; size_bytes: number } | null;
  last_phone: string | null;
  last_education: string | null;
};

export const CAREER_LEVELS: Record<string, string> = {
  INTERN: "Intern",
  TRAINEE: "Trainee",
  JUNIOR: "Junior",
  MID_LEVEL: "Mid level",
  SENIOR: "Senior",
  LEAD: "Lead",
};
export const EMPLOYMENT_TYPES: Record<string, string> = {
  FULL_TIME: "Full time",
  PART_TIME: "Part time",
  CONTRACT: "Contract",
  INTERNSHIP: "Internship",
};
export const SECTORS = ["IT", "HR", "Management", "Agriculture", "Other"] as const;
export const EDUCATION_OPTIONS = [
  "G.C.E. O/L",
  "G.C.E. A/L",
  "Diploma / HND",
  "Undergraduate (studying)",
  "Bachelor's degree",
  "Master's degree",
] as const;

export class JobsError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

const UNAVAILABLE = "The jobs service can't be reached right now. Please try again shortly.";

/** A request to the jobs service as the logged-in user. Throws JobsError with a readable message. */
export async function jobsFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) throw new JobsError("Log in first.", 401);
  let response: Response;
  try {
    response = await fetch(`${API_GATEWAY_URL}/jobs${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        ...(init.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
        Authorization: `Bearer ${token}`,
      },
    });
  } catch {
    throw new JobsError(UNAVAILABLE, 503);
  }
  if (!response.ok) throw await errorFrom(response);
  return response;
}

async function errorFrom(response: Response): Promise<JobsError> {
  if (response.status >= 502) return new JobsError(UNAVAILABLE, response.status);
  const body = await response.json().catch(() => null);
  const detail = body?.detail;
  if (typeof detail === "string") return new JobsError(detail, response.status);
  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") {
    return new JobsError(String(detail[0].msg).replace(/^Value error, /, ""), response.status);
  }
  return new JobsError("Something went wrong. Please try again.", response.status);
}

export async function jobsJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  return (await (await jobsFetch(path, init)).json()) as T;
}

/** The caller's company, or null when the account has no company yet. */
export async function getMyCompany(): Promise<Company | null> {
  try {
    return await jobsJson<Company>("/company");
  } catch (error) {
    if (error instanceof JobsError && error.status === 404) return null;
    throw error;
  }
}

/** Live jobs and the student's applications, for Market Pulse. Null when the service isn't available. */
export async function getJobsForStudent(): Promise<{ jobs: Job[]; mine: MyApplications } | null> {
  try {
    const [jobs, mine] = await Promise.all([jobsJson<Job[]>("/vacancies"), jobsJson<MyApplications>("/applications")]);
    return { jobs, mine };
  } catch {
    return null;
  }
}

export function formatDay(iso: string | null): string {
  if (!iso) return "No closing date";
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

/** "today", "yesterday", "3 days ago" or a date, in Sri Lanka time. */
export function dayAgo(iso: string | null): string {
  if (!iso) return "";
  const day = (value: Date) => value.toLocaleDateString("en-CA", { timeZone: "Asia/Colombo" });
  const then = new Date(iso);
  const days = Math.round((Date.parse(day(new Date())) - Date.parse(day(then))) / 86_400_000);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 7) return `${days} days ago`;
  return then.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "Asia/Colombo" });
}

export function fileSize(bytes: number | null | undefined): string {
  if (!bytes) return "";
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export function isEmailLink(link: string): boolean {
  return !/^https?:\/\//i.test(link) && link.includes("@");
}
