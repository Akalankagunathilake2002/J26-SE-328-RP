import type { Metadata } from "next";

import { ComingSoon } from "@/components/pages/ComingSoon";

export const metadata: Metadata = { title: "Mock Interview — Skillaro" };

export default function MockInterviewPage() {
  return (
    <ComingSoon
      path="/mock-interview"
      title="Mock Interview"
      description="Follow personalized learning recommendations and practice with AI-powered mock interviews to build career confidence."
    />
  );
}
