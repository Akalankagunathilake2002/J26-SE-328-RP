import { Briefcase, Clock, Plus, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { JobStatusButton } from "@/components/company/CompanyActions";
import { JOB_STATE, Pill, plural } from "@/components/jobs/ui";
import { getMyCompanyCached } from "@/lib/companyPortal";
import { CAREER_LEVELS, EMPLOYMENT_TYPES, formatDay, jobsJson, type Job } from "@/lib/jobs";

export default async function CompanyDashboardPage({ searchParams }: PageProps<"/company">) {
  const result = await getMyCompanyCached();
  if (result.status !== "ok" || !result.company) return null;
  const company = result.company;
  const saved = (await searchParams).saved;
  let jobs: Job[] = [];
  let loadError: string | null = null;
  try {
    jobs = await jobsJson<Job[]>("/company/vacancies");
  } catch {
    loadError = "Your job posts can't be loaded right now. Please try again shortly.";
  }

  const count = (...states: Job["state"][]) => jobs.filter((j) => states.includes(j.state)).length;
  const tiles = [
    { label: "Live on Skillaro", value: count("LIVE"), note: "Students can see these" },
    { label: "Waiting for verification", value: count("WAITING"), note: "Published, not shown yet" },
    { label: "New applicants", value: company.new_applicants ?? 0, note: "Not opened yet" },
    { label: "Drafts", value: count("DRAFT"), note: "Only your company sees these" },
    { label: "Closed", value: count("CLOSED", "EXPIRED"), note: "No longer shown" },
  ];
  const firstName = (company.contact_name ?? "").split(/\s+/)[0] || "there";

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-[34px] leading-tight font-semibold sm:text-[36px]">
            Good to see you, <em className="text-[#5b3df5]">{firstName}</em>
          </h1>
          <p className="mt-1 text-[15px] text-[#5a5663]">Post jobs and see where each one stands.</p>
        </div>
        <Link
          href="/company/jobs/new"
          className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-[#5b3df5] px-[18px] text-sm font-bold text-white shadow-[0_8px_20px_-8px_rgba(91,61,245,0.6)] hover:bg-[#4a2fd0] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30"
        >
          <Plus className="size-[18px]" aria-hidden="true" />
          Post a job
        </Link>
      </div>

      {saved === "published" || saved === "draft" ? (
        <p role="status" className="rounded-2xl border border-[#bfe8cb] bg-[#eefbf1] px-4 py-3 text-sm font-medium text-[#123d22]">
          {saved === "draft"
            ? "Saved as a draft. Only your company can see it."
            : company.status === "VERIFIED"
              ? "Published. Students can see it on the Jobs page."
              : "Published. Students will see it after a Skillaro admin verifies your company."}
        </p>
      ) : null}

      {company.status === "PENDING" && (
        <Banner tone="amber" Icon={Clock}>
          <strong>{company.name} is waiting for verification.</strong> You can post jobs now. Students see them after a Skillaro admin has checked your company.
        </Banner>
      )}
      {company.status === "VERIFIED" && (
        <Banner tone="green" Icon={ShieldCheck}>
          <strong>{company.name} is verified.</strong> Your published jobs are live for students on the Jobs page. Students apply on Skillaro, and you see them under Applicants.
        </Banner>
      )}
      {company.status === "REJECTED" && (
        <Banner tone="red">
          <strong>Skillaro couldn&apos;t verify {company.name}.</strong> Your jobs stay hidden from students. Correct your company details under Company profile, or contact the Skillaro team.
        </Banner>
      )}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        {tiles.map((t) => (
          <div key={t.label} className="flex flex-col gap-1.5 rounded-2xl border border-[#e4dfd5] bg-white px-4 py-3.5">
            <span className="text-[13px] font-bold text-[#3b3845]">{t.label}</span>
            <span className="font-display text-[34px] leading-none font-semibold">{t.value}</span>
            <span className="text-xs text-[#5a5663]">{t.note}</span>
          </div>
        ))}
      </div>

      <section className="overflow-hidden rounded-[18px] border border-[#e4dfd5] bg-white">
        <div className="flex items-center justify-between gap-3 px-[18px] py-4">
          <h2 className="text-[17px] font-extrabold">Your job posts</h2>
          <span className="text-[13px] text-[#5a5663]">{plural(jobs.length, "post")}</span>
        </div>
        {loadError ? (
          <p className="border-t border-[#efebe3] px-[18px] py-6 text-sm text-[#5a5663]">{loadError}</p>
        ) : jobs.length === 0 ? (
          <div className="flex flex-col items-center gap-2.5 border-t border-[#efebe3] px-[18px] pt-8 pb-10 text-center">
            <span className="grid size-[52px] place-items-center rounded-2xl bg-[#efe8ff] text-[#4a2fd0]">
              <Briefcase className="size-6" aria-hidden="true" />
            </span>
            <p className="text-base font-extrabold">No job posts yet</p>
            <p className="max-w-[400px] text-sm leading-normal text-[#5a5663]">
              Write a job description and Skillaro finds the skills in it. You choose which ones are required.
            </p>
            <Link href="/company/jobs/new" className="mt-1 inline-flex min-h-9 items-center rounded-[10px] bg-[#5b3df5] px-3 text-[13px] font-bold text-white hover:bg-[#4a2fd0]">
              Post your first job
            </Link>
          </div>
        ) : (
          <ul>
            {jobs.map((job) => (
              <li key={job.vacancy_id} className="flex flex-wrap items-center gap-x-4 gap-y-2.5 border-t border-[#efebe3] px-[18px] py-3.5">
                <div className="flex min-w-0 flex-[1_1_260px] flex-col gap-1">
                  <span className="text-[15px] font-extrabold">{job.title}</span>
                  <span className="text-[13px] text-[#5a5663]">
                    {[CAREER_LEVELS[job.career_level ?? ""], EMPLOYMENT_TYPES[job.employment_type ?? ""], job.location].filter(Boolean).join(" · ")}
                  </span>
                </div>
                <span className="flex-[0_1_170px] text-[13px] text-[#5a5663]">
                  {job.required.length} required · {job.preferred.length} preferred
                </span>
                <span className="flex-[0_1_150px] text-[13px] text-[#5a5663]">
                  {job.closing_date ? `Closes ${formatDay(job.closing_date)}` : "No closing date"}
                </span>
                {(job.applicants ?? 0) > 0 ? (
                  <Link
                    href={`/company/applicants?job=${job.vacancy_id}`}
                    className="inline-flex min-h-9 items-center rounded-[10px] bg-[#d0ffa4] px-3 text-[13px] font-bold text-[#1f3a00] hover:bg-[#bff58a]"
                  >
                    {plural(job.applicants ?? 0, "applicant")}
                    {(job.new_applicants ?? 0) > 0 && ` · ${job.new_applicants} new`}
                  </Link>
                ) : (
                  <span className="text-[13px] text-[#5a5663]">No applicants yet</span>
                )}
                <Pill tone={JOB_STATE[job.state].tone}>{JOB_STATE[job.state].label}</Pill>
                <div className="flex items-start gap-2">
                  <Link
                    href={`/company/jobs/${job.vacancy_id}/edit`}
                    className="inline-flex min-h-9 items-center rounded-[10px] border border-[#ddd7cb] bg-white px-3 text-[13px] font-bold hover:border-[#b9b1a2]"
                  >
                    Edit
                  </Link>
                  <JobStatusButton vacancyId={job.vacancy_id} status={job.status} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Banner({ tone, Icon, children }: { tone: "amber" | "green" | "red"; Icon?: typeof Clock; children: React.ReactNode }) {
  const tones = {
    amber: "border-[#f1dca6] bg-[#fff8e6] text-[#4a3500]",
    green: "border-[#bfe8cb] bg-[#eefbf1] text-[#123d22]",
    red: "border-[#efc4c4] bg-[#fdf0f0] text-[#5e1d1d]",
  };
  return (
    <div className={`flex items-start gap-3 rounded-[18px] border px-[18px] py-4 text-sm leading-normal ${tones[tone]}`}>
      {Icon && <Icon className="mt-0.5 size-[22px] shrink-0" aria-hidden="true" />}
      <p>{children}</p>
    </div>
  );
}
