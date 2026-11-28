import { CompanyReviewButtons } from "@/components/company/CompanyActions";
import { Avatar, Pill, plural } from "@/components/jobs/ui";
import { requireAdmin } from "@/lib/auth";
import { dayAgo, jobsJson, type Company } from "@/lib/jobs";

export const metadata = {
  title: "Companies — Skillaro Admin",
  description: "Verify the companies that post jobs on Skillaro.",
};

export default async function AdminCompaniesPage() {
  await requireAdmin("/admin/companies");
  let companies: Company[] = [];
  let loadError = false;
  try {
    companies = await jobsJson<Company[]>("/admin/companies");
  } catch {
    loadError = true;
  }
  const pending = companies.filter((c) => c.status === "PENDING");
  const verified = companies.filter((c) => c.status === "VERIFIED");
  const rejected = companies.filter((c) => c.status === "REJECTED");

  return (
    <div className="flex flex-col gap-4 text-[#1d1b24]">
      <div>
        <h1 className="font-display text-[32px] leading-tight font-semibold">
          Companies to <em className="text-[#5b3df5]">verify</em>
        </h1>
        <p className="mt-1 text-[15px] text-[#5a5663]">
          A company&apos;s jobs stay hidden from students until an admin verifies it. This is done once per company.
        </p>
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-2 rounded-[18px] border border-[#ddd2ff] bg-[#f7f5ff] px-[18px] py-3.5 text-sm text-[#2c2545]">
        <strong>What to check</strong>
        <span>1. The website is real and belongs to the company</span>
        <span>2. The email uses the website&apos;s domain</span>
        <span>3. The jobs look like real jobs</span>
      </div>

      {loadError ? (
        <p className="rounded-[18px] border border-[#e4dfd5] bg-white p-6 text-center text-sm">
          Companies can&apos;t be loaded right now. The jobs service isn&apos;t reachable.
        </p>
      ) : (
        <>
          {pending.length === 0 ? (
            <p className="rounded-[18px] border border-[#e4dfd5] bg-white p-6 text-center text-sm text-[#3b3845]">Nothing waiting. New companies show up here.</p>
          ) : (
            <ul className="grid gap-3.5 md:grid-cols-2">
              {pending.map((c) => (
                <li key={c.company_id} className="flex flex-col gap-3.5 rounded-[18px] border border-[#e4dfd5] bg-white p-[18px]">
                  <div className="flex items-center gap-3">
                    <Avatar name={c.name} id={c.company_id} />
                    <div className="min-w-0 flex-1">
                      <p className="text-base font-extrabold">{c.name}</p>
                      <p className="text-[13px] text-[#5a5663]">{[c.sector, c.city].filter(Boolean).join(" · ")}</p>
                    </div>
                    <Pill tone="amber">Waiting</Pill>
                  </div>
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-2.5 text-[13px]">
                    <Fact label="Website">
                      {c.website ? (
                        <a href={/^https?:\/\//i.test(c.website) ? c.website : `https://${c.website}`} target="_blank" rel="noopener noreferrer" className="text-[#4a2fd0] underline-offset-2 hover:underline">
                          {c.website}
                        </a>
                      ) : (
                        "Not given"
                      )}
                    </Fact>
                    <Fact label="Signed up by">{c.contact_name}</Fact>
                    <Fact label="Work email">{c.contact_email}</Fact>
                    <Fact label="Signed up">{dayAgo(c.created_at)}</Fact>
                  </dl>
                  {c.description && <p className="text-[13px] leading-normal text-[#3b3845]">{c.description}</p>}
                  <div className="flex flex-wrap items-start justify-between gap-2.5">
                    <CompanyReviewButtons companyId={c.company_id} status={c.status} name={c.name} />
                    <span className="text-[13px] text-[#5a5663]">
                      {plural(c.published ?? 0, "job")} waiting{(c.drafts ?? 0) > 0 && `, ${plural(c.drafts ?? 0, "draft")}`}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <CompanyList title="Verified companies" companies={verified} tone="green" label={(c) => `${plural(c.published ?? 0, "live job")}`} />
          {rejected.length > 0 && <CompanyList title="Rejected" companies={rejected} tone="red" label={() => "Jobs hidden"} />}
        </>
      )}
    </div>
  );
}

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-[#5a5663]">{label}</dt>
      <dd className="font-bold break-all">{children}</dd>
    </div>
  );
}

function CompanyList({ title, companies, tone, label }: { title: string; companies: Company[]; tone: "green" | "red"; label: (c: Company) => string }) {
  return (
    <section className="overflow-hidden rounded-[18px] border border-[#e4dfd5] bg-white">
      <div className="flex items-center justify-between gap-3 px-[18px] py-4">
        <h2 className="text-[17px] font-extrabold">{title}</h2>
        <span className="text-[13px] text-[#5a5663]">{plural(companies.length, "company", "companies")}</span>
      </div>
      {companies.length === 0 ? (
        <p className="border-t border-[#efebe3] px-[18px] py-4 text-sm text-[#5a5663]">None yet.</p>
      ) : (
        <ul>
          {companies.map((c) => (
            <li key={c.company_id} className="flex flex-wrap items-center gap-x-4 gap-y-2.5 border-t border-[#efebe3] px-[18px] py-3.5">
              <Avatar name={c.name} id={c.company_id} size="sm" />
              <div className="min-w-0 flex-[1_1_220px]">
                <p className="text-sm font-extrabold">{c.name}</p>
                <p className="text-[13px] text-[#5a5663]">
                  {[c.sector, c.city, c.contact_email].filter(Boolean).join(" · ")}
                </p>
              </div>
              <span className="text-[13px] text-[#5a5663]">
                {c.status === "VERIFIED" ? `Verified ${dayAgo(c.verified_at)}` : `Rejected ${dayAgo(c.rejected_at)}`}
              </span>
              <Pill tone={tone}>{label(c)}</Pill>
              <CompanyReviewButtons companyId={c.company_id} status={c.status} name={c.name} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
