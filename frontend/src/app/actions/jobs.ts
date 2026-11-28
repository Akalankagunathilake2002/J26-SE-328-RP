"use server";

import { refresh } from "next/cache";
import { redirect } from "next/navigation";

import { AuthServiceError, getCurrentUser, registerAccount, startSession } from "@/lib/auth";
import {
  JobsError,
  jobsFetch,
  jobsJson,
  SECTORS,
  type ApplicationStatus,
  type DetectedSkills,
  type JobInput,
} from "@/lib/jobs";

// Company job posts: company sign-up and portal, admin review, and students applying (see lib/jobs.ts).

export type FormState =
  | { errors?: Record<string, string>; message?: string; saved?: boolean; values?: Record<string, string> }
  | undefined;

export type Result = { error?: string };

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const WEB_PATTERN = /^(https?:\/\/)?[a-z0-9-]+(\.[a-z0-9-]+)+(:\d+)?(\/\S*)?$/i;

function read(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value.trim() : "";
}

function messageOf(error: unknown): string {
  return error instanceof JobsError || error instanceof AuthServiceError ? error.message : "Something went wrong. Please try again.";
}

function companyFields(formData: FormData) {
  return {
    name: read(formData, "companyName"),
    website: read(formData, "website"),
    sector: read(formData, "sector"),
    city: read(formData, "city"),
    description: read(formData, "description"),
  };
}

function companyErrors(fields: ReturnType<typeof companyFields>): Record<string, string> {
  const errors: Record<string, string> = {};
  if (fields.name.length < 2) errors.companyName = "Enter the company name.";
  if (fields.website && !WEB_PATTERN.test(fields.website)) errors.website = "Enter a web address, for example yourcompany.lk.";
  if (!(SECTORS as readonly string[]).includes(fields.sector)) errors.sector = "Choose a sector.";
  return errors;
}

function companyBody(fields: ReturnType<typeof companyFields>) {
  return JSON.stringify({
    name: fields.name,
    website: fields.website || null,
    sector: fields.sector,
    city: fields.city || null,
    description: fields.description || null,
  });
}

/** A new company account: the person's login (role hr), then the company, waiting for an admin. */
export async function registerCompany(_state: FormState, formData: FormData): Promise<FormState> {
  const fields = companyFields(formData);
  const fullName = read(formData, "fullName");
  const email = read(formData, "email");
  const password = formData.get("password");
  const values = { ...fields, companyName: fields.name, fullName, email };

  const errors = companyErrors(fields);
  if (fullName.length < 2) errors.fullName = "Enter your name.";
  if (!EMAIL_PATTERN.test(email)) errors.email = "Enter your work email.";
  if (typeof password !== "string" || password.length < 8) errors.password = "Use at least 8 characters.";
  if (Object.keys(errors).length > 0) return { errors, values };

  try {
    await registerAccount(fullName, email, password as string, "company");
    await startSession(email, password as string);
  } catch (error) {
    return { message: messageOf(error), values };
  }
  try {
    await jobsFetch("/company", { method: "POST", body: companyBody(fields) });
  } catch {
    // The account exists; the portal asks for the company details again.
  }
  redirect("/company");
}

/** The company details, for a company account that has none yet. */
export async function createCompanyProfile(_state: FormState, formData: FormData): Promise<FormState> {
  const fields = companyFields(formData);
  const errors = companyErrors(fields);
  if (Object.keys(errors).length > 0) return { errors, values: { ...fields, companyName: fields.name } };
  try {
    await jobsFetch("/company", { method: "POST", body: companyBody(fields) });
  } catch (error) {
    return { message: messageOf(error), values: { ...fields, companyName: fields.name } };
  }
  redirect("/company");
}

export async function updateCompanyProfile(_state: FormState, formData: FormData): Promise<FormState> {
  const fields = companyFields(formData);
  const errors = companyErrors(fields);
  if (Object.keys(errors).length > 0) return { errors, values: { ...fields, companyName: fields.name } };
  try {
    await jobsFetch("/company", { method: "PATCH", body: companyBody(fields) });
  } catch (error) {
    return { message: messageOf(error), values: { ...fields, companyName: fields.name } };
  }
  refresh();
  return { saved: true };
}

export async function findJobSkills(title: string, description: string): Promise<DetectedSkills | Result> {
  try {
    return await jobsJson<DetectedSkills>("/company/skills", { method: "POST", body: JSON.stringify({ title, description }) });
  } catch (error) {
    return { error: messageOf(error) };
  }
}

/** Saves a job post (new, or an edit of `vacancyId`) and goes back to the dashboard. */
export async function saveJob(vacancyId: string | null, input: JobInput): Promise<Result> {
  try {
    await jobsFetch(vacancyId ? `/company/vacancies/${encodeURIComponent(vacancyId)}` : "/company/vacancies", {
      method: vacancyId ? "PUT" : "POST",
      body: JSON.stringify(input),
    });
  } catch (error) {
    return { error: messageOf(error) };
  }
  redirect(`/company?saved=${input.status === "PUBLISHED" ? "published" : "draft"}`);
}

export async function setJobStatus(vacancyId: string, status: "DRAFT" | "PUBLISHED" | "CLOSED"): Promise<Result> {
  try {
    await jobsFetch(`/company/vacancies/${encodeURIComponent(vacancyId)}`, { method: "PATCH", body: JSON.stringify({ status }) });
  } catch (error) {
    return { error: messageOf(error) };
  }
  refresh();
  return {};
}

export async function setApplicantStatus(applicationId: string, status: Exclude<ApplicationStatus, "NEW">): Promise<Result> {
  try {
    await jobsFetch(`/company/applications/${encodeURIComponent(applicationId)}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  } catch (error) {
    return { error: messageOf(error) };
  }
  refresh();
  return {};
}

/** Admin: verify, reject or reopen (back to waiting) a company. */
export async function reviewCompany(companyId: string, action: "verify" | "reject" | "reopen"): Promise<Result> {
  const user = await getCurrentUser();
  if (user?.role !== "admin") return { error: "Only admins can do this." };
  try {
    await jobsFetch(`/admin/companies/${encodeURIComponent(companyId)}/${action}`, { method: "POST" });
  } catch (error) {
    return { error: messageOf(error) };
  }
  refresh();
  return {};
}

/** A student applies on Skillaro: phone, education, note, consent and a CV (PDF), or the last CV again. */
export async function applyForJob(_state: FormState, formData: FormData): Promise<FormState> {
  const vacancyId = read(formData, "vacancyId");
  const phone = read(formData, "phone");
  const education = read(formData, "education");
  const note = read(formData, "note");
  const consent = formData.get("consent") === "on";
  const cv = formData.get("cv");
  const hasFile = cv instanceof File && cv.size > 0;
  const reuse = formData.get("reuseCv") === "on";
  const values = { phone, education, note };

  const errors: Record<string, string> = {};
  if (!/^\+?[0-9][0-9 ()-]{6,18}[0-9]$/.test(phone)) errors.phone = "Enter a phone number, for example 077 123 4567.";
  if (!hasFile && !reuse) errors.cv = "Add your CV as a PDF.";
  if (hasFile && cv.size > 2 * 1024 * 1024) errors.cv = "Your CV must be 2 MB or smaller.";
  if (hasFile && cv.type && cv.type !== "application/pdf") errors.cv = "Your CV must be a PDF file.";
  if (note.length > 1000) errors.note = "Keep the note under 1,000 characters.";
  if (!consent) errors.consent = "Tick the box to agree to share your details.";
  if (Object.keys(errors).length > 0) return { errors, values };

  const body = new FormData();
  body.set("phone", phone);
  body.set("consent", "true");
  if (education) body.set("education", education);
  if (note) body.set("note", note);
  if (hasFile) body.set("cv", cv, cv.name);
  try {
    await jobsFetch(`/vacancies/${encodeURIComponent(vacancyId)}/applications`, { method: "POST", body });
  } catch (error) {
    return { message: messageOf(error), values };
  }
  refresh();
  return { saved: true };
}

export async function withdrawApplication(applicationId: string): Promise<Result> {
  try {
    await jobsFetch(`/applications/${encodeURIComponent(applicationId)}`, { method: "DELETE" });
  } catch (error) {
    return { error: messageOf(error) };
  }
  refresh();
  return {};
}
