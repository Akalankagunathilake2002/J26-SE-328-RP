import type { Metadata } from "next";

import { Navbar } from "@/components/home/Navbar";
import {
  DecorativeBackground,
  HeroSection,
  OverviewCards,
  ProgressAndMatches,
  RecentAnalysisHistory,
  StartAnalysisPanel,
} from "@/components/skill-analysis";

export const metadata: Metadata = {
  title: "Career Readiness Analysis — Skillaro",
  description:
    "See how your skills align with your selected role and discover your path to growth.",
};

// Career Readiness Analysis dashboard page displaying the static UI skeleton
export default function SkillAnalysisPage() {
  return (
    <div className="min-h-screen bg-page text-ink relative overflow-x-hidden">
      <Navbar currentPath="/skill-analysis" />
      <DecorativeBackground />

      <main className="relative z-10 max-w-[880px] mx-auto px-4 sm:px-6 py-6 sm:py-8 flex flex-col gap-6">
        <div>
          <HeroSection />
          <StartAnalysisPanel />
        </div>
        <OverviewCards />
        <ProgressAndMatches />
        <RecentAnalysisHistory />
      </main>
    </div>
  );
}
