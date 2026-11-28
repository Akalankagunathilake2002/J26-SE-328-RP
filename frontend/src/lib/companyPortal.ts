import "server-only";

import { cache } from "react";

import { getMyCompany, JobsError, type Company } from "@/lib/jobs";

export type CompanyResult = { status: "ok"; company: Company | null } | { status: "error"; message: string };

/** The logged-in company account's company, once per request (the portal layout and its pages both need it). */
export const getMyCompanyCached = cache(async (): Promise<CompanyResult> => {
  try {
    return { status: "ok", company: await getMyCompany() };
  } catch (error) {
    return { status: "error", message: error instanceof JobsError ? error.message : "Please try again shortly." };
  }
});
