import type { ReactNode } from "react";

import { CompanySidebarNav } from "@/components/company/CompanySidebar";
import { Footer } from "@/components/home/Footer";
import { Navbar } from "@/components/home/Navbar";
import { Avatar, COMPANY_STATUS, Pill } from "@/components/jobs/ui";
import type { Company } from "@/lib/jobs";

/**
 * The company portal's frame, like Market Pulse: a full-height dark column on the left (on wide screens a dark
 * strip under it reaches the footer, and the column stays in view while the page scrolls); on phones a dark bar
 * whose links scroll sideways. The shared site header stays as it is.
 */
export function CompanyPortalShell({
  company,
  user,
  children,
}: {
  company: Pick<Company, "company_id" | "name" | "sector" | "city" | "status" | "new_applicants">;
  user: { full_name: string; email: string };
  children: ReactNode;
}) {
  const status = COMPANY_STATUS[company.status];
  return (
    <div className="min-h-screen bg-[#f4f2ee] text-[#1d1b24] lg:bg-[linear-gradient(to_right,#17161d_250px,#f4f2ee_250px)]">
      <Navbar currentPath="/company" />
      <div className="lg:flex">
        <aside aria-label="Company portal" className="bg-[#17161d] text-white lg:w-[250px] lg:shrink-0">
          <div className="flex flex-col gap-4 px-3 py-4 lg:sticky lg:top-[86px] lg:h-[calc(100vh-86px)] lg:gap-5 lg:overflow-y-auto lg:py-5">
            <div className="flex items-center gap-3 px-2">
              <Avatar name={company.name} id={company.company_id} />
              <div className="min-w-0">
                <p className="truncate text-[15px] font-bold">{company.name}</p>
                <p className="truncate text-xs text-[#b9b4c6]">{[company.sector, company.city].filter(Boolean).join(" · ")}</p>
              </div>
            </div>
            <Pill tone={status.tone} className="mx-2 self-start">
              {status.label}
            </Pill>
            <CompanySidebarNav newApplicants={company.new_applicants ?? 0} />
            <div className="mt-auto hidden rounded-xl border border-[#2f2d3a] bg-[#23212c] px-3 py-3 text-xs leading-relaxed text-[#a9a7b6] lg:block">
              <p className="font-bold text-white">Signed in as {user.full_name}</p>
              <p className="break-all">{user.email}</p>
            </div>
          </div>
        </aside>
        <main className="min-w-0 flex-1 px-4 py-5 sm:px-6 lg:px-8 lg:py-6">
          <div className="mx-auto max-w-[1200px]">{children}</div>
        </main>
      </div>
      <Footer />
    </div>
  );
}
