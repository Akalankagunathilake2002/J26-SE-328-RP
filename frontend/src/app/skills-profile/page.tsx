import type { Metadata } from "next";

import { Navbar } from "@/components/home/Navbar";
import { SkillsProfileBuilder } from "@/components/skills-profile/SkillsProfileBuilder";
import { requireUser } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Skills Profile — Skillaro",
  description:
    "Turn your projects, academic work, certificates, CV, and experience into a clear, evidence-backed skill profile.",
};

// C02 Evidence-Based Skill Profile: protected page for the logged-in user
export default async function SkillsProfilePage() {
  const user = await requireUser("/skills-profile");
  const firstName = user.full_name.trim().split(/\s+/)[0] || "there";

  return (
    <div className="min-h-screen bg-page text-ink">
      <Navbar currentPath="/skills-profile" />
      <main className="mx-auto max-w-[980px] px-4 py-6 sm:px-6 sm:py-8">
        <SkillsProfileBuilder userId={user.id} firstName={firstName} />
      </main>
    </div>
  );
}
