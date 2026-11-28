import { CompanyDetailsForm } from "@/components/company/CompanyForms";
import { COMPANY_STATUS, Pill } from "@/components/jobs/ui";
import { getMyCompanyCached } from "@/lib/companyPortal";

export default async function CompanyProfilePage() {
  const result = await getMyCompanyCached();
  if (result.status !== "ok" || !result.company) return null;
  const company = result.company;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="font-display text-[34px] leading-tight font-semibold sm:text-[36px]">
          Company <em className="text-[#5b3df5]">profile</em>
        </h1>
        <Pill tone={COMPANY_STATUS[company.status].tone}>{COMPANY_STATUS[company.status].label}</Pill>
      </div>
      <section className="rounded-[18px] border border-[#e4dfd5] bg-white p-5 sm:p-6">
        <CompanyDetailsForm company={company} />
      </section>
      <section className="grid gap-4 rounded-[18px] border border-[#e4dfd5] bg-white p-5 sm:grid-cols-2 sm:p-6">
        <div>
          <p className="text-[13px] font-semibold text-[#5a5663]">Account holder</p>
          <p className="mt-1 text-[15px] font-bold">{company.contact_name}</p>
        </div>
        <div>
          <p className="text-[13px] font-semibold text-[#5a5663]">Work email</p>
          <p className="mt-1 text-[15px] font-bold break-all">{company.contact_email}</p>
        </div>
      </section>
      <p className="text-sm leading-normal text-[#5a5663]">
        Changing the company name or website sends the company back for verification, so a verified company can&apos;t turn into a different one.
      </p>
    </div>
  );
}
