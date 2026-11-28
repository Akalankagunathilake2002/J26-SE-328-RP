import { ArrowUpRight, Briefcase, CheckCircle2, Search, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { WithdrawButton } from "@/components/company/CompanyActions";
import { APPLICATION_STATUS, Avatar, MetaChip, Pill, plural, SkillChip } from "@/components/jobs/ui";
import type { User } from "@/lib/auth";
import { CAREER_LEVELS, dayAgo, EMPLOYMENT_TYPES, formatDay, isEmailLink, type Job, type MyApplications } from "@/lib/jobs";

import { ApplyPanel } from "./ApplyPanel";

// The Jobs page (/jobs): live jobs that verified companies posted on Skillaro, and the student's applications.

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`rounded-[18px] border border-[#e4dfd5] bg-white ${className}`}>{children}</section>;
}

export type JobsQuery = { q: string; industry: string; level: string; job: string };

function jobsHref(query: JobsQuery, change: Partial<JobsQuery>): string {
  const next = { ...query, ...change };
  const params = new URLSearchParams();
  if (next.q) params.set("q", next.q);
  if (next.industry) params.set("industry", next.industry);
  if (next.level) params.set("level", next.level);
  if (next.job) params.set("job", next.job);
  const s = params.toString();
  return `/jobs${s ? `?${s}` : ""}`;
}

const NEW_FOR_DAYS = 3;

function isNew(job: Job): boolean {
  return job.published_at !== null && Date.now() - Date.parse(job.published_at) < NEW_FOR_DAYS * 86_400_000;
}

export function JobsView({ jobs, mine, query, user }: { jobs: Job[]; mine: MyApplications; query: JobsQuery; user: User }) {
  const needle = query.q.trim().toLowerCase();
  const industries = [...new Set(jobs.map((j) => j.company.sector).filter((s): s is string => !!s))].sort();
  const levels = Object.keys(CAREER_LEVELS).filter((l) => jobs.some((j) => j.career_level === l));
  const shown = jobs.filter(
    (j) =>
      (!query.industry || j.company.sector === query.industry) &&
      (!query.level || j.career_level === query.level) &&
      (!needle || [j.title, j.company.name, ...j.required, ...j.preferred].some((t) => t.toLowerCase().includes(needle))),
  );
  const selected = shown.find((j) => j.vacancy_id === query.job) ?? shown[0] ?? null;

  if (jobs.length === 0) {
    return (
      <Card className="flex flex-col items-center gap-2 px-6 py-10 text-center">
        <span className="grid size-12 place-items-center rounded-2xl bg-[#efe8ff] text-[#4a2fd0]">
          <Briefcase className="size-6" aria-hidden="true" />
        </span>
        <p className="text-base font-bold">No company jobs yet</p>
        <p className="max-w-[440px] text-sm text-[#5a5663]">
          Jobs that verified companies post on Skillaro show up here. Check back soon, or see what the job market asks for in{" "}
          <Link href="/market-pulse?view=skills" className="font-semibold text-[#4a2fd0] underline underline-offset-4">
            Market Pulse
          </Link>
          .
        </p>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Card className="flex flex-wrap items-end gap-x-6 gap-y-3.5 px-4 py-3.5">
        <form action="/jobs" className="flex min-w-[220px] flex-[1_1_240px] flex-col gap-1.5" role="search">
          {query.industry && <input type="hidden" name="industry" value={query.industry} />}
          {query.level && <input type="hidden" name="level" value={query.level} />}
          <label htmlFor="job-search" className="text-[13px] font-bold text-[#3b3845]">
            Search
          </label>
          <div className="flex gap-2">
            <input
              id="job-search"
              name="q"
              defaultValue={query.q}
              placeholder="Job, company or skill"
              className="min-h-10 w-full rounded-[10px] border border-[#d9d3c6] bg-white px-3 text-sm outline-none focus:border-[#5b3df5] focus:ring-4 focus:ring-[#5b3df5]/15"
            />
            <button type="submit" aria-label="Search jobs" className="grid size-10 shrink-0 place-items-center rounded-[10px] bg-[#17161d] text-white hover:bg-[#2b2934]">
              <Search className="size-4" aria-hidden="true" />
            </button>
          </div>
        </form>
        <FilterGroup label="Industry">
          <Filter href={jobsHref(query, { industry: "", job: "" })} on={!query.industry}>
            All
          </Filter>
          {industries.map((s) => (
            <Filter key={s} href={jobsHref(query, { industry: s, job: "" })} on={query.industry === s}>
              {s}
            </Filter>
          ))}
        </FilterGroup>
        <FilterGroup label="Career level">
          <Filter href={jobsHref(query, { level: "", job: "" })} on={!query.level}>
            All
          </Filter>
          {levels.map((l) => (
            <Filter key={l} href={jobsHref(query, { level: l, job: "" })} on={query.level === l}>
              {CAREER_LEVELS[l]}
            </Filter>
          ))}
        </FilterGroup>
      </Card>

      <div className="flex flex-wrap items-start gap-4">
        <div className="flex min-w-0 flex-[1_1_320px] flex-col gap-2.5">
          <span className="text-[13px] text-[#5a5663]">{plural(shown.length, "open job")}</span>
          {shown.length === 0 && (
            <Card className="p-6 text-center text-sm">
              No jobs match these filters.{" "}
              <Link href="/jobs" className="font-semibold text-[#4a2fd0] underline underline-offset-4">
                Show all jobs
              </Link>
            </Card>
          )}
          <ul className="flex flex-col gap-2.5">
            {shown.map((j) => {
              const on = selected?.vacancy_id === j.vacancy_id;
              const more = j.required.length + j.preferred.length - Math.min(4, j.required.length);
              return (
                <li key={j.vacancy_id}>
                  <Link
                    href={jobsHref(query, { job: j.vacancy_id })}
                    prefetch={false}
                    scroll={false}
                    aria-current={on ? "true" : undefined}
                    className={`flex flex-col gap-2.5 rounded-2xl border bg-white p-3.5 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5b3df5] ${
                      on ? "border-[#5b3df5] shadow-[0_0_0_3px_#e7e0ff]" : "border-[#e4dfd5] hover:border-[#c9c2b3]"
                    }`}
                  >
                    <span className="flex items-start gap-3">
                      <Avatar name={j.company.name} id={j.company.company_id} />
                      <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                        <span className="text-[15px] font-extrabold">{j.title}</span>
                        <span className="text-[13px] text-[#5a5663]">
                          {j.company.name}
                          {j.location && ` · ${j.location}`}
                        </span>
                      </span>
                      {j.application_status ? <Pill tone="purple">Applied</Pill> : isNew(j) ? <Pill tone="lime">New</Pill> : null}
                    </span>
                    <span className="flex flex-wrap gap-1.5">
                      {j.career_level && <MetaChip>{CAREER_LEVELS[j.career_level]}</MetaChip>}
                      {j.employment_type && <MetaChip>{EMPLOYMENT_TYPES[j.employment_type]}</MetaChip>}
                      <MetaChip>{j.closing_date ? `Closes ${formatDay(j.closing_date)}` : "No closing date"}</MetaChip>
                    </span>
                    <span className="flex flex-wrap gap-1.5">
                      {j.required.slice(0, 4).map((s) => (
                        <SkillChip key={s} name={s} />
                      ))}
                      {more > 0 && <MetaChip>+{more} more</MetaChip>}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>

        {selected && <JobDetail job={selected} mine={mine} user={user} />}
      </div>
    </div>
  );
}

function JobDetail({ job, mine, user }: { job: Job; mine: MyApplications; user: User }) {
  const experience = job.minimum_years == null ? "Not stated" : job.minimum_years === 0 ? "None needed" : `${job.minimum_years}+ years`;
  const meta: [string, string][] = [
    ["Career level", CAREER_LEVELS[job.career_level ?? ""] ?? "Not stated"],
    ["Job type", EMPLOYMENT_TYPES[job.employment_type ?? ""] ?? "Not stated"],
    ["Location", job.location ?? "Not stated"],
    ["Closes", formatDay(job.closing_date)],
    ["Experience", experience],
    ["Education", job.education ?? "Not stated"],
  ];
  const application = mine.applications.find((a) => a.vacancy_id === job.vacancy_id);

  return (
    <article aria-label={job.title} className="flex min-w-0 flex-[1.3_1_420px] flex-col gap-[18px] rounded-[18px] border border-[#e4dfd5] bg-white p-[22px]">
      <header className="flex items-start gap-3.5">
        <Avatar name={job.company.name} id={job.company.company_id} size="lg" />
        <div className="flex min-w-0 flex-1 flex-col gap-1.5">
          <h2 className="font-display text-[28px] leading-tight font-semibold">{job.title}</h2>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-bold">{job.company.name}</span>
            <Pill tone="green">
              <ShieldCheck className="size-3.5" aria-hidden="true" />
              Verified company
            </Pill>
            {job.published_at && <span className="text-[#5a5663]">Posted {dayAgo(job.published_at)}</span>}
          </div>
        </div>
      </header>
      <dl className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
        {meta.map(([label, value]) => (
          <div key={label} className="rounded-xl bg-[#f7f5f0] px-3 py-2.5">
            <dt className="text-xs font-semibold text-[#5a5663]">{label}</dt>
            <dd className="mt-0.5 text-sm font-bold">{value}</dd>
          </div>
        ))}
      </dl>
      <SkillSection title="Required skills" skills={job.required} />
      {job.preferred.length > 0 && <SkillSection title="Preferred skills" skills={job.preferred} preferred />}
      {job.certifications.length > 0 && (
        <section className="flex flex-col gap-2">
          <h3 className="text-sm font-extrabold">Certificates and licences</h3>
          <div className="flex flex-wrap gap-1.5">
            {job.certifications.map((c) => (
              <MetaChip key={c}>{c}</MetaChip>
            ))}
          </div>
        </section>
      )}
      {job.description && (
        <section className="flex flex-col gap-2">
          <h3 className="text-sm font-extrabold">About the job</h3>
          <p className="text-sm leading-relaxed whitespace-pre-line text-[#2c2935]">{job.description}</p>
        </section>
      )}

      {user.role !== "user" ? (
        <p className="border-t border-[#efebe3] pt-4 text-[13px] text-[#5a5663]">Only student accounts can apply. You&apos;re logged in with a company or admin account.</p>
      ) : application ? (
        <Applied job={job} applicationId={application.application_id} appliedAt={application.applied_at} />
      ) : (
        <ApplyPanel
          key={job.vacancy_id}
          vacancyId={job.vacancy_id}
          companyName={job.company.name}
          name={user.full_name}
          email={user.email}
          lastCv={mine.last_cv}
          lastPhone={mine.last_phone}
          lastEducation={mine.last_education}
        />
      )}
    </article>
  );
}

function Applied({ job, applicationId, appliedAt }: { job: Job; applicationId: string; appliedAt: string }) {
  const st = APPLICATION_STATUS[job.application_status ?? "NEW"];
  const email = job.apply_url ? isEmailLink(job.apply_url) : false;
  return (
    <div className="flex flex-col gap-3 border-t border-[#efebe3] pt-4">
      <div className="flex items-start gap-3 rounded-2xl border border-[#bfe8cb] bg-[#eefbf1] px-4 py-3.5 text-sm leading-normal text-[#123d22]">
        <CheckCircle2 className="mt-0.5 size-5 shrink-0" aria-hidden="true" />
        <div className="flex flex-col gap-1.5">
          <span className="flex flex-wrap items-center gap-2">
            <strong>You applied {dayAgo(appliedAt)}</strong>
            <Pill tone={st.studentTone}>{st.student}</Pill>
          </span>
          <span>
            {job.company.name} can see your name, contact details, education, CV and note. Follow it under{" "}
            <Link href="/jobs?tab=applications" className="font-semibold underline underline-offset-2">
              My applications
            </Link>
            .
          </span>
        </div>
      </div>
      {job.apply_url && (
        <div className="flex flex-wrap items-center gap-2.5 text-sm">
          <span>Optional: {job.company.name} also uses its own application page.</span>
          <a
            href={email ? `mailto:${job.apply_url}` : job.apply_url}
            target={email ? undefined : "_blank"}
            rel="noopener noreferrer"
            className="inline-flex min-h-9 items-center gap-1.5 rounded-[10px] border border-[#ddd7cb] bg-white px-3 text-[13px] font-bold hover:border-[#b9b1a2]"
          >
            {email ? "Apply by email" : "Apply on company site"}
            <ArrowUpRight className="size-3.5" aria-hidden="true" />
          </a>
        </div>
      )}
      <div>
        <WithdrawButton applicationId={applicationId} small={false} />
      </div>
    </div>
  );
}

function SkillSection({ title, skills, preferred = false }: { title: string; skills: string[]; preferred?: boolean }) {
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-sm font-extrabold">{title}</h3>
      <div className="flex flex-wrap gap-1.5">
        {skills.map((s) => (
          <SkillChip key={s} name={s} preferred={preferred} />
        ))}
      </div>
    </section>
  );
}

export function ApplicationsView({ mine }: { mine: MyApplications }) {
  if (mine.applications.length === 0) {
    return (
      <Card className="flex flex-col items-center gap-2.5 px-6 py-10 text-center">
        <p className="text-base font-bold">You haven&apos;t applied for a job yet</p>
        <p className="max-w-[420px] text-sm text-[#5a5663]">Open a job and press Apply. You see exactly what the company gets before you send.</p>
        <Link href="/jobs" className="mt-1 inline-flex min-h-9 items-center rounded-[10px] bg-[#5b3df5] px-3 text-[13px] font-bold text-white hover:bg-[#4a2fd0]">
          Browse jobs
        </Link>
      </Card>
    );
  }
  return (
    <div className="flex flex-col gap-3">
      <Card className="overflow-hidden">
        <ul>
          {mine.applications.map((a, i) => {
            const st = APPLICATION_STATUS[a.status];
            return (
              <li key={a.application_id} className={`flex flex-wrap items-center gap-x-4 gap-y-2.5 px-4 py-3.5 ${i > 0 ? "border-t border-[#efebe3]" : ""}`}>
                <Avatar name={a.company_name} id={a.company_id} />
                <div className="flex min-w-0 flex-[1_1_240px] flex-col gap-0.5">
                  <span className="text-[15px] font-extrabold">{a.title}</span>
                  <span className="text-[13px] text-[#5a5663]">
                    {[a.company_name, a.location, `Applied ${dayAgo(a.applied_at)}`].filter(Boolean).join(" · ")}
                  </span>
                </div>
                <Pill tone={st.studentTone}>{st.student}</Pill>
                {a.job_open ? (
                  <Link
                    href={`/jobs?job=${a.vacancy_id}`}
                    className="inline-flex min-h-9 items-center rounded-[10px] border border-[#ddd7cb] bg-white px-3 text-[13px] font-bold hover:border-[#b9b1a2]"
                  >
                    View job
                  </Link>
                ) : (
                  <span className="text-[13px] text-[#5a5663]">Job closed</span>
                )}
                <WithdrawButton applicationId={a.application_id} />
              </li>
            );
          })}
        </ul>
      </Card>
      <p className="text-[13px] leading-normal text-[#5a5663]">
        Withdrawing removes your details from the company&apos;s list. Your skill profile and readiness results are never shared with companies.
      </p>
    </div>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-[13px] font-bold text-[#3b3845]">{label}</span>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function Filter({ href, on, children }: { href: string; on: boolean; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      prefetch={false}
      aria-current={on ? "true" : undefined}
      className={`inline-flex min-h-9 items-center rounded-full border px-3 text-[13px] font-semibold transition-colors ${
        on ? "border-[#c9b8ff] bg-[#efe8ff] text-[#3d24b8]" : "border-[#ddd7cb] bg-white text-[#3b3845] hover:border-[#b9b1a2]"
      }`}
    >
      {children}
    </Link>
  );
}
