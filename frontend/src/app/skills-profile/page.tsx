import type { Metadata } from "next";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata: Metadata = { title: "Skills Profile — Skillaro" };

export default function SkillsProfilePage() {
  return (
    <ComingSoon
      path="/skills-profile"
      title="Skills Profile"
      description="Turn your projects, academic work, certificates, CV, and experience into a clear, evidence-backed skill profile."
    />
  );
}
