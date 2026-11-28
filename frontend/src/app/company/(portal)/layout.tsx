import { CloudOff } from "lucide-react";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { CompanyDetailsForm } from "@/components/company/CompanyForms";
import { CompanyPortalShell } from "@/components/company/CompanyPortalShell";
import { Footer } from "@/components/home/Footer";
import { Navbar } from "@/components/home/Navbar";
import { requireCompanyUser } from "@/lib/auth";
import { getMyCompanyCached } from "@/lib/companyPortal";

export const metadata: Metadata = { title: "Company portal — Skillaro" };

/** The company portal: a dark sidebar beside the page, under the shared site header. */
export default async function CompanyPortalLayout({ children }: { children: ReactNode }) {
  const user = await requireCompanyUser("/company");
  const result = await getMyCompanyCached();

  const company = result.status === "ok" ? result.company : null;

  if (company) {
    return (
      <CompanyPortalShell company={company} user={user}>
        {children}
      </CompanyPortalShell>
    );
  }

  return (
    <div className="min-h-screen bg-[#f4f2ee] text-[#1d1b24]">
      <Navbar currentPath="/company" />
      <div className="mx-auto flex max-w-[1440px] flex-col gap-5 px-4 pt-5 pb-12 sm:px-6">
        {result.status === "ok" ? (
          <main className="mx-auto w-full max-w-[760px]">
            <div className="rounded-[18px] border border-[#e4dfd5] bg-white p-6 sm:p-7">
              <h1 className="font-display text-[32px] leading-tight font-semibold">
                Add your <em className="text-[#5b3df5]">company</em>
              </h1>
              <p className="mt-1.5 mb-5 text-[15px] text-[#5a5663]">
                Your account is ready. Add the company you hire for; a Skillaro admin checks it before students see its jobs.
              </p>
              <CompanyDetailsForm />
            </div>
          </main>
        ) : (
          <main className="mx-auto w-full max-w-[760px]">
            <div className="flex items-start gap-3 rounded-[18px] border border-[#e4dfd5] bg-white p-6">
              <CloudOff className="mt-0.5 size-6 shrink-0 text-[#5a5663]" aria-hidden="true" />
              <div>
                <h1 className="text-lg font-bold">The company portal can&apos;t be loaded right now</h1>
                <p className="mt-1 text-[15px] text-[#5a5663]">{result.message}</p>
              </div>
            </div>
          </main>
        )}
      </div>
      <Footer />
    </div>
  );
}
