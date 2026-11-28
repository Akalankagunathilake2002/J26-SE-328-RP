import { FileText, Mail, Users } from "lucide-react";
import Link from "next/link";

import { ApplicantStatusButtons, MarkSeen } from "@/components/company/CompanyActions";
import { APPLICATION_STATUS, Avatar, Pill, plural } from "@/components/jobs/ui";
import { getMyCompanyCached } from "@/lib/companyPortal";
import { dayAgo, fileSize, JobsError, jobsJson, type Applicant, type ApplicationStatus, type Job } from "@/lib/jobs";

const STATUS_FILTERS: [string, string][] = [
  ["", "All"],
  ["NEW", "New"],
  ["SEEN", "Seen"],
  ["SHORTLISTED", "Shortlisted"],
  ["NOT_SELECTED", "Not selected"],
];

type Query = { job: string; status: string; id: string };

function href(q: Query, change: Partial<Query>): string {
  const next = { ...q, ...change };
  const params = new URLSearchParams();
  if (next.job) params.set("job", next.job);
  if (next.status) params.set("status", next.status);
  if (next.id) params.set("id", next.id);
  const s = params.toString();
  return `/company/applicants${s ? `?${s}` : ""}`;
}

function first(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? "";
}

export default async function ApplicantsPage({ searchParams }: PageProps<"/company/applicants">) {
  const result = await getMyCompanyCached();
  if (result.status !== "ok" || !result.company) return null;
  const params = await searchParams;
  const q: Query = { job: first(params.job), status: first(params.status), id: first(params.id) };
  if (!(q.status in APPLICATION_STATUS)) q.status = "";

  const [all, jobs, selected] = await Promise.all([
    jobsJson<Applicant[]>("/company/applications"),
    jobsJson<Job[]>("/company/vacancies"),
    q.id
      ? jobsJson<Applicant>(`/company/applications/${encodeURIComponent(q.id)}`).catch((error) => {
          if (error instanceof JobsError && (error.status === 404 || error.status === 422)) return null;
          throw error;
        })
      : null,
  ]);
  const shown = all.filter((a) => (!q.job || a.vacancy_id === q.job) && (!q.status || a.status === q.status));
  const jobsWithApplicants = jobs.filter((j) => all.some((a) => a.vacancy_id === j.vacancy_id));
  const verified = result.company.status === "VERIFIED";

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="font-display text-[34px] leading-tight font-semibold sm:text-[36px]">
          Your <em className="text-[#5b3df5]">applicants</em>
        </h1>
        <p className="mt-1 text-[15px] leading-normal text-[#5a5663]">
          Students who applied on Skillaro. You see only what each student agreed to share: name, contact details, education, CV and a note.
        </p>
      </div>

      {all.length === 0 ? (
        <div className="flex flex-col items-center gap-2.5 rounded-[18px] border border-[#e4dfd5] bg-white px-[18px] pt-8 pb-10 text-center">
          <span className="grid size-[52px] place-items-center rounded-2xl bg-[#efe8ff] text-[#4a2fd0]">
            <Users className="size-6" aria-hidden="true" />
          </span>
          <p className="text-base font-extrabold">No applicants yet</p>
          <p className="max-w-[460px] text-sm leading-normal text-[#5a5663]">
            {!verified
              ? "Students can apply once your company is verified and a job is published."
              : jobs.some((j) => j.state === "LIVE")
                ? "When a student applies to one of your live jobs, they show up here."
                : "Publish a job first. Students who apply to it show up here."}
          </p>
        </div>
      ) : (
        <>
          <nav aria-label="Filter applicants" className="flex flex-wrap gap-x-7 gap-y-3.5 rounded-[18px] border border-[#e4dfd5] bg-white px-4 py-3.5">
            <FilterRow label="Job">
              <FilterLink href={href(q, { job: "", id: "" })} on={!q.job}>
                All jobs
              </FilterLink>
              {jobsWithApplicants.map((j) => (
                <FilterLink key={j.vacancy_id} href={href(q, { job: j.vacancy_id, id: "" })} on={q.job === j.vacancy_id}>
                  {j.title} ({all.filter((a) => a.vacancy_id === j.vacancy_id).length})
                </FilterLink>
              ))}
            </FilterRow>
            <FilterRow label="Status">
              {STATUS_FILTERS.map(([value, label]) => (
                <FilterLink key={label} href={href(q, { status: value, id: "" })} on={q.status === value}>
                  {label}
                </FilterLink>
              ))}
            </FilterRow>
          </nav>

          <div className="flex flex-wrap items-start gap-4">
            <div className="flex min-w-0 flex-[1_1_300px] flex-col gap-2">
              <span className="text-[13px] text-[#5a5663]">{plural(shown.length, "applicant")}</span>
              {shown.length === 0 && (
                <p className="rounded-[18px] border border-[#e4dfd5] bg-white p-5 text-center text-sm text-[#3b3845]">No applicants match these filters.</p>
              )}
              <ul className="flex flex-col gap-2">
                {shown.map((a) => {
                  const st = APPLICATION_STATUS[a.status];
                  const on = selected?.application_id === a.application_id;
                  return (
                    <li key={a.application_id}>
                      <Link
                        href={href(q, { id: a.application_id })}
                        prefetch={false}
                        aria-current={on ? "true" : undefined}
                        className={`flex items-center gap-3 rounded-2xl border bg-white p-3.5 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5b3df5] ${
                          on ? "border-[#5b3df5] shadow-[0_0_0_3px_#e7e0ff]" : "border-[#e4dfd5] hover:border-[#c9c2b3]"
                        }`}
                      >
                        <Avatar name={a.full_name} id={a.application_id} size="sm" />
                        <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                          <span className="text-[15px] font-extrabold">{a.full_name}</span>
                          <span className="truncate text-[13px] text-[#5a5663]">
                            {a.job_title} · {dayAgo(a.applied_at)}
                          </span>
                        </span>
                        <Pill tone={st.tone}>{st.company}</Pill>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>

            {selected ? (
              <ApplicantDetail applicant={selected} />
            ) : (
              <div className="flex min-w-0 flex-[1.4_1_420px] flex-col items-center gap-2 rounded-[18px] border border-dashed border-[#e4dfd5] bg-[#fbfaf7] px-6 py-10 text-center">
                <p className="text-base font-extrabold">Choose an applicant</p>
                <p className="max-w-[360px] text-sm leading-normal text-[#5a5663]">
                  Their details open here. Opening an application marks it Seen, and the student can see that.
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function ApplicantDetail({ applicant: a }: { applicant: Applicant }) {
  const st = APPLICATION_STATUS[a.status as ApplicationStatus];
  const firstName = a.full_name.split(/\s+/)[0] || a.full_name;
  return (
    <section aria-label={`${a.full_name}'s application`} className="flex min-w-0 flex-[1.4_1_420px] flex-col gap-[18px] rounded-[18px] border border-[#e4dfd5] bg-white p-[22px]">
      <MarkSeen applicationId={a.application_id} status={a.status} />
      <div className="flex items-start gap-3.5">
        <Avatar name={a.full_name} id={a.application_id} size="lg" />
        <div className="flex min-w-0 flex-1 flex-col gap-1.5">
          <h2 className="font-display text-[28px] leading-tight font-semibold">{a.full_name}</h2>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span>
              Applied for <strong>{a.job_title}</strong>
            </span>
            <span className="text-[#5a5663]">· {dayAgo(a.applied_at)}</span>
            <Pill tone={st.tone}>{st.company}</Pill>
          </div>
        </div>
      </div>
      <dl className="grid gap-2.5 sm:grid-cols-2">
        <Info label="Email">
          <a href={`mailto:${a.email}`} className="break-all text-[#4a2fd0] underline-offset-2 hover:underline">
            {a.email}
          </a>
        </Info>
        <Info label="Phone">
          <a href={`tel:${a.phone.replace(/[^\d+]/g, "")}`} className="text-[#4a2fd0] underline-offset-2 hover:underline">
            {a.phone}
          </a>
        </Info>
        <Info label="Education" wide>
          {a.education || "Not given"}
        </Info>
      </dl>
      {a.cv_file_name && (
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-[#e4dfd5] px-3.5 py-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-[#fdecec] text-[#a12626]">
            <FileText className="size-5" aria-hidden="true" />
          </span>
          <span className="flex min-w-0 flex-[1_1_180px] flex-col gap-0.5">
            <span className="text-sm font-bold break-all">{a.cv_file_name}</span>
            <span className="text-xs text-[#5a5663]">CV · PDF · {fileSize(a.cv_size_bytes)}</span>
          </span>
          <a
            href={`/company/applicants/${a.application_id}/cv`}
            target="_blank"
            rel="noopener"
            className="inline-flex min-h-9 items-center rounded-[10px] border border-[#ddd7cb] bg-white px-3 text-[13px] font-bold hover:border-[#b9b1a2]"
          >
            Open CV
          </a>
        </div>
      )}
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-extrabold">Note from the student</h3>
        <p className="text-sm leading-relaxed whitespace-pre-line text-[#2c2935]">{a.note || "No note."}</p>
      </div>
      <div className="flex flex-col gap-2.5 border-t border-[#efebe3] pt-4">
        <div className="flex flex-wrap items-start gap-2.5">
          <ApplicantStatusButtons applicationId={a.application_id} status={a.status} firstName={firstName} />
          <a
            href={`mailto:${a.email}?subject=${encodeURIComponent(`Your application for ${a.job_title}`)}`}
            className="inline-flex min-h-9 items-center gap-1.5 rounded-[10px] border border-[#ddd7cb] bg-white px-3 text-[13px] font-bold hover:border-[#b9b1a2]"
          >
            <Mail className="size-4" aria-hidden="true" />
            Email {firstName}
          </a>
        </div>
        <p className="text-[13px] leading-normal text-[#5a5663]">
          The student sees: <strong className="text-[#24212c]">{st.student}</strong>. If they withdraw, their details are removed from this list.
        </p>
      </div>
    </section>
  );
}

function Info({ label, wide, children }: { label: string; wide?: boolean; children: React.ReactNode }) {
  return (
    <div className={`rounded-xl bg-[#f7f5f0] px-3 py-2.5 ${wide ? "sm:col-span-2" : ""}`}>
      <dt className="text-xs font-semibold text-[#5a5663]">{label}</dt>
      <dd className="mt-0.5 text-sm font-bold">{children}</dd>
    </div>
  );
}

function FilterRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-[13px] font-bold text-[#3b3845]">{label}</span>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function FilterLink({ href, on, children }: { href: string; on: boolean; children: React.ReactNode }) {
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
