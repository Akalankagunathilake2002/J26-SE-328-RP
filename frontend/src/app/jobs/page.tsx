import { Briefcase } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { Footer } from "@/components/home/Footer";
import { Navbar } from "@/components/home/Navbar";
import { ApplicationsView, JobsView } from "@/components/jobs/JobsViews";
import { requireUser } from "@/lib/auth";
import { getJobsForStudent } from "@/lib/jobs";

export const metadata: Metadata = { title: "Jobs — Skillaro" };

const PATH = "/jobs";

function first(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? "";
}

/** Jobs that verified companies posted on Skillaro, and (for students) their own applications. */
export default async function JobsPage({ searchParams }: PageProps<"/jobs">) {
  const user = await requireUser(PATH);
  const params = await searchParams;
  const student = user.role === "user";
  const tab = student && first(params.tab) === "applications" ? "applications" : "jobs";
  const hiring = await getJobsForStudent();

  const tabs = [
    { key: "jobs", label: "All jobs", href: PATH, count: hiring?.jobs.length },
    ...(student ? [{ key: "applications", label: "My applications", href: `${PATH}?tab=applications`, count: hiring?.mine.applications.length }] : []),
  ];

  return (
    <div className="min-h-screen bg-[#f4f2ee] text-[#1d1b24]">
      <Navbar currentPath={PATH} />
      <main className="mx-auto flex max-w-[1280px] flex-col gap-4 px-4 pt-6 pb-12 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
          <div className="min-w-0">
            <h1 className="font-display text-[34px] leading-tight font-semibold sm:text-[38px]">
              Jobs from <em className="text-[#5b3df5]">verified companies</em>
            </h1>
            <p className="mt-1 max-w-[720px] text-[15px] leading-normal text-[#5a5663]">
              Posted on Skillaro by companies we have checked. Their skills use the same names as Market Pulse, so you can see what each job asks for.
            </p>
          </div>
          {tabs.length > 1 && (
            <nav aria-label="Jobs" className="flex gap-1.5">
              {tabs.map((t) => (
                <Link
                  key={t.key}
                  href={t.href}
                  aria-current={tab === t.key ? "page" : undefined}
                  className={`inline-flex min-h-10 items-center gap-2 rounded-full border px-4 text-sm font-bold transition-colors focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30 ${
                    tab === t.key ? "border-[#17161d] bg-[#17161d] text-white" : "border-[#ddd7cb] bg-white text-[#3b3845] hover:border-[#b9b1a2]"
                  }`}
                >
                  {t.label}
                  {t.count != null && (
                    <span className={`rounded-full px-2 text-xs ${tab === t.key ? "bg-[#d0ffa4] text-[#1f3a00]" : "bg-[#f1eee8] text-[#46433c]"}`}>{t.count}</span>
                  )}
                </Link>
              ))}
            </nav>
          )}
        </div>

        {!hiring ? (
          <div className="flex items-start gap-3 rounded-[18px] border border-[#e4dfd5] bg-white p-6">
            <Briefcase className="mt-0.5 size-6 shrink-0 text-[#5a5663]" aria-hidden="true" />
            <div>
              <h2 className="text-lg font-bold">Jobs can&apos;t be loaded right now</h2>
              <p className="mt-1 text-[15px] text-[#5a5663]">The jobs service isn&apos;t reachable. Please try again shortly.</p>
            </div>
          </div>
        ) : tab === "applications" ? (
          <ApplicationsView mine={hiring.mine} />
        ) : (
          <JobsView
            jobs={hiring.jobs}
            mine={hiring.mine}
            user={user}
            query={{ q: first(params.q), industry: first(params.industry), level: first(params.level), job: first(params.job) }}
          />
        )}
      </main>
      <Footer />
    </div>
  );
}
