import type { Metadata } from "next";

import { Navbar } from "@/components/home/Navbar";
import { requireUser } from "@/lib/auth";
import {
  DecorativeBackground,
  SkillAnalysisDashboard,
} from "@/components/skill-analysis";

export const metadata: Metadata = {
  title: "Career Readiness Analysis — Skillaro",
  description:
    "See how your skills align with your selected role and discover your path to growth.",
};

// Career Readiness Analysis protected page requiring authenticated user session
export default async function SkillAnalysisPage() {
  const user = await requireUser("/skill-analysis");
  const firstName = user.full_name.trim().split(/\s+/)[0] || "Student";

  return (
    <div className="min-h-screen bg-page text-ink relative overflow-x-hidden">
      <Navbar currentPath="/skill-analysis" />
      <DecorativeBackground />

      <main className="relative max-w-[880px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <SkillAnalysisDashboard userId={user.id} firstName={firstName} />
      </main>
    </div>
  );
}
