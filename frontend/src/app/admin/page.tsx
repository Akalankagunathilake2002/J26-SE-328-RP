import Link from "next/link";
import Image from "next/image";
import { requireAdmin } from "@/lib/auth";
import { Layers, Clock, ArrowRight, ShieldCheck } from "lucide-react";

export const metadata = {
  title: "Admin Portal — Skillaro",
  description: "Skillaro administration portal entry point.",
};

export default async function AdminDashboardPage() {
  await requireAdmin("/admin");

  return (
    <div className="relative space-y-4 sm:space-y-5">
      {/* Hero container with floating action dashes */}
      <div className="relative">

        {/* Dashboard Hero Card */}
        <div className="relative flex flex-col justify-between gap-4 overflow-hidden rounded-2xl border-2 border-ink bg-[#E2D9FC] p-4.5 sm:p-5 md:flex-row md:items-center shadow-[4px_4px_0px_#0d0d0d]">
          <div className="max-w-md space-y-2">
            <div className="inline-flex items-center gap-1.5 rounded-md border-2 border-ink bg-[#D4F7C5] px-2 py-0.5 text-[10px] font-black uppercase tracking-wider text-ink">
              <ShieldCheck className="size-3 text-ink" />
              Administration Console
            </div>
            <h2 className="text-2xl font-black tracking-tight text-ink sm:text-3xl">
              Skillaro Admin Portal
            </h2>
            <p className="text-xs sm:text-sm font-medium leading-relaxed text-ink/80">
              Select a management module below to administer the Shared Skill Knowledge Base or review proposed taxonomy candidates.
            </p>
          </div>

          <div className="relative flex shrink-0 items-center justify-center md:justify-end">
            <Image src="/admin/ssk-illustration.png" alt="Skillaro Admin Portal Illustration" width={340} height={170} className="h-28 w-auto object-contain sm:h-34 md:h-38" priority unoptimized
            />
          </div>
        </div>
      </div>

      {/* Two Core Management Modules */}
      <div className="grid grid-cols-1 items-stretch gap-4 sm:gap-5 md:grid-cols-2">
        {/* Module 1: Shared Knowledge Management */}
        <div className="flex h-full flex-col justify-between rounded-2xl border-2 border-ink bg-[#D6F5EC] p-4.5 sm:p-5 shadow-[4px_4px_0px_#0d0d0d]">
          <div>
            <div className="flex items-start gap-2">
              <div className="flex size-11 items-center justify-center rounded-xl border-2 border-ink bg-[#7DF9FF] shadow-[2px_2px_0px_#0d0d0d]">
                <Layers className="size-5.5 text-ink" />
              </div>
            </div>

            <h3 className="mt-3 text-lg font-black text-ink sm:text-xl">
              Shared Knowledge Management
            </h3>
            <p className="mt-1.5 text-xs sm:text-sm font-medium leading-relaxed text-ink/80">
              Manage canonical industry domains, career roles, skills taxonomy, and verified graph relationships across 4 interactive tabs.
            </p>
          </div>

          <div className="mt-4 pt-1">
            <Link
              href="/admin/knowledge"
              className="flex w-full items-center justify-between rounded-xl border-2 border-ink bg-white px-3.5 py-2.5 text-xs sm:text-sm font-black text-ink shadow-[3px_3px_0px_#0d0d0d] transition-all hover:-translate-y-0.5 hover:shadow-[4px_4px_0px_#0d0d0d] active:translate-y-0"
            >
              <span>Open Knowledge Manager</span>
              <ArrowRight className="size-4 text-ink" />
            </Link>
          </div>
        </div>

        {/* Module 2: Candidate Management */}
        <div className="flex h-full flex-col justify-between rounded-2xl border-2 border-ink bg-[#FEF3C7] p-4.5 sm:p-5 shadow-[4px_4px_0px_#0d0d0d]">
          <div>
            <div className="flex items-start gap-2">
              <div className="flex size-11 items-center justify-center rounded-xl border-2 border-ink bg-[#FFE66D] shadow-[2px_2px_0px_#0d0d0d]">
                <Clock className="size-5.5 text-ink" />
              </div>
            </div>

            <h3 className="mt-3 text-lg font-black text-ink sm:text-xl">
              Candidate Management
            </h3>
            <p className="mt-1.5 text-xs sm:text-sm font-medium leading-relaxed text-ink/80">
              Review and verify or reject proposed relationship candidates and inspect incoming entity submissions.
            </p>
          </div>

          <div className="mt-4 pt-1">
            <Link
              href="/admin/candidates"
              className="flex w-full items-center justify-between rounded-xl border-2 border-ink bg-white px-3.5 py-2.5 text-xs sm:text-sm font-black text-ink shadow-[3px_3px_0px_#0d0d0d] transition-all hover:-translate-y-0.5 hover:shadow-[4px_4px_0px_#0d0d0d] active:translate-y-0"
            >
              <span>Open Candidate Reviews</span>
              <ArrowRight className="size-4 text-ink" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
