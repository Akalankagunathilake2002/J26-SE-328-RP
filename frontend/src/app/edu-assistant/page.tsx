import type { Metadata } from "next";

import { Navbar } from "@/components/home/Navbar";
import { Footer } from "@/components/home/Footer";
import { requireUser } from "@/lib/auth";
import EduAssistantClient from "@/components/mock-interview/EduAssistantClient";

export const metadata: Metadata = {
  title: "Skillaro Edu Assistant — Skillaro",
  description: "Chat with Skillaro about your curriculum, or learn a topic step by step with quizzes built on Bloom's taxonomy.",
};

export default async function EduAssistantPage() {
  const user = await requireUser("/edu-assistant");

  return (
    <div className="flex min-h-screen flex-col bg-page">
      <Navbar currentPath="/edu-assistant" />
      <main className="flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <EduAssistantClient studentId={user.id} studentName={user.full_name || user.email} />
      </main>
      <Footer />
    </div>
  );
}
