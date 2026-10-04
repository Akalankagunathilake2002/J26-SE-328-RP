import type { Metadata } from "next";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata: Metadata = { title: "Skill Analysis — Skillaro" };

export default function SkillAnalysisPage() {
  return (
    <ComingSoon
      path="/skill-analysis"
      title="Skill Analysis"
      description="Understand your career readiness and discover where you can improve."
    />
  );
}
