import { JobsError, jobsFetch } from "@/lib/jobs";

/** An applicant's CV, for the company the application was sent to (C01 checks that). */
export async function GET(_request: Request, ctx: RouteContext<"/company/applicants/[id]/cv">) {
  const { id } = await ctx.params;
  try {
    const response = await jobsFetch(`/company/applications/${encodeURIComponent(id)}/cv`);
    return new Response(response.body, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": response.headers.get("content-disposition") ?? "inline",
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch (error) {
    const status = error instanceof JobsError ? error.status : 500;
    return new Response(error instanceof JobsError ? error.message : "Something went wrong.", { status });
  }
}
