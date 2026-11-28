"use client";

import { Briefcase, Building2, LayoutDashboard, Users } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/company", label: "Dashboard", Icon: LayoutDashboard },
  { href: "/company/jobs/new", label: "Post a job", Icon: Briefcase },
  { href: "/company/applicants", label: "Applicants", Icon: Users, badge: true },
  { href: "/company/profile", label: "Company profile", Icon: Building2 },
];

/** The company portal's own menu (the site header stays as it is). */
export function CompanySidebarNav({ newApplicants }: { newApplicants: number }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Company">
      <ul className="flex gap-1 overflow-x-auto lg:flex-col lg:overflow-visible">
        {items.map(({ href, label, Icon, badge }) => {
          const current = href === "/company" ? pathname === "/company" : pathname.startsWith(href) || (href === "/company/jobs/new" && pathname.startsWith("/company/jobs"));
          return (
            <li key={href} className="shrink-0">
              <Link
                href={href}
                aria-current={current ? "page" : undefined}
                className={`flex min-h-11 items-center gap-2.5 rounded-xl px-3 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d0ffa4] ${
                  current ? "bg-[#2b2934] text-[#d0ffa4]" : "text-[#cfcbd8] hover:bg-[#24222c] hover:text-white"
                }`}
              >
                <Icon className="size-[18px] shrink-0" aria-hidden="true" />
                <span className="whitespace-nowrap">{label}</span>
                {badge && newApplicants > 0 && (
                  <span className="ml-auto rounded-full bg-[#d0ffa4] px-2 text-xs font-bold text-[#1f3a00]" aria-label={`${newApplicants} new`}>
                    {newApplicants}
                  </span>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
