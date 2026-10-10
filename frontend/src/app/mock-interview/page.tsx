import type { Metadata } from "next";

import { Navbar } from "@/components/home/Navbar";
import { Footer } from "@/components/home/Footer";
import { getCurrentUser } from "@/lib/auth";
import MockInterviewClient from "@/components/mock-interview/MockInterviewClient";

export const metadata: Metadata = {
  title: "Mock Interview & AI Learning Assistant — Skillaro",
  description:
    "Practice face-to-face AI mock technical interviews with Elena Vance and receive personalized learning guidance grounded in RAG.",
};

export default async function MockInterviewPage() {
  const user = await getCurrentUser();

  return (
    <div className="flex min-h-screen flex-col bg-page">
      <Navbar currentPath="/mock-interview" />
      <main className="flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <MockInterviewClient user={user} />
      </main>
      <Footer />
    </div>
  );
}

