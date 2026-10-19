import Link from "next/link";
import { requireAdmin } from "@/lib/auth";
import { Layers, Clock, ArrowRight, ShieldCheck } from "lucide-react";

export const metadata = {
  title: "Admin Portal — Skillaro",
  description: "Skillaro administration portal entry point.",
};

export default async function AdminDashboardPage() {
  await requireAdmin("/admin");

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="hard-shadow rounded-2xl border-2 border-ink bg-[#fff9f2] p-6 sm:p-8">
        <div className="max-w-xl space-y-2">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-ink bg-[#d0ffa4] px-2.5 py-0.5 text-xs font-black uppercase tracking-wider text-ink">
            <ShieldCheck className="size-3.5" />
            Administration Console
          </div>
          <h2 className="text-2xl font-black text-ink sm:text-3xl">
            Skillaro Admin Portal
          </h2>
          <p className="text-xs text-muted sm:text-sm">
            Select a management module below to administer the Shared Skill Knowledge Base or review proposed taxonomy candidates.
          </p>
        </div>
      </div>

      {/* Two Core Management Modules */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {/* Module 1: Shared Knowledge Management */}
        <Link
          href="/admin/knowledge"
          className="hard-shadow group flex flex-col justify-between rounded-xl border-2 border-ink bg-white p-6 transition-all hover:-translate-y-1 hover:bg-[#fff9f2]"
        >
          <div>
            <div className="hard-shadow-sm flex size-12 items-center justify-center rounded-lg border-2 border-ink bg-[#7df9ff]">
              <Layers className="size-6 text-ink" />
            </div>
            <h3 className="mt-4 text-lg font-black text-ink">
              Shared Knowledge Management
            </h3>
            <p className="mt-1 text-xs text-muted">
              Manage canonical industry domains, career roles, skills taxonomy, and verified graph relationships across 4 interactive tabs.
            </p>
          </div>

          <div className="mt-6 flex items-center justify-between border-t-2 border-ink/10 pt-4 text-xs font-bold text-ink group-hover:text-brand-blue">
            <span>Open Knowledge Manager</span>
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
          </div>
        </Link>

        {/* Module 2: Candidate Management */}
        <Link
          href="/admin/candidates"
          className="hard-shadow group flex flex-col justify-between rounded-xl border-2 border-ink bg-white p-6 transition-all hover:-translate-y-1 hover:bg-[#fff9f2]"
        >
          <div>
            <div className="hard-shadow-sm flex size-12 items-center justify-center rounded-lg border-2 border-ink bg-[#ffde4d]">
              <Clock className="size-6 text-ink" />
            </div>
            <h3 className="mt-4 text-lg font-black text-ink">
              Candidate Management
            </h3>
            <p className="mt-1 text-xs text-muted">
              Review and verify or reject proposed relationship candidates and inspect incoming entity submissions.
            </p>
          </div>

          <div className="mt-6 flex items-center justify-between border-t-2 border-ink/10 pt-4 text-xs font-bold text-ink group-hover:text-brand-blue">
            <span>Open Candidate Reviews</span>
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
          </div>
        </Link>
      </div>
    </div>
  );
}
