"use client";

import React, { useState } from "react";
import { Mic, BookOpen, Activity, Sparkles, ChevronRight } from "lucide-react";
import StudentContextBanner from "./StudentContextBanner";
import InterviewStudio from "./InterviewStudio";
import PersonalizedLearningView from "./PersonalizedLearningView";
import VivaInspectorView from "./VivaInspectorView";
import type { User } from "@/lib/auth";

interface MockInterviewClientProps {
  user?: User | null;
}

export default function MockInterviewClient({ user }: MockInterviewClientProps) {
  const [activeTab, setActiveTab] = useState<"interview" | "learning" | "inspector">("interview");

  const studentName = user?.full_name || "Dilmith";
  const studentId = user?.id ? `stu_${user.id.slice(0, 6)}` : "stu_1024";
  const targetRole = "Backend Developer";
  const studentSkills = ["Java", "Spring Boot", "MySQL"];
  const learningPriority = "Database Connection Management & Scalability";

  return (
    <div className="mx-auto max-w-[1440px] space-y-6">
      {/* Top Banner with Student Context */}
      <StudentContextBanner
        studentId={studentId}
        studentName={studentName}
        targetRole={targetRole}
        skills={studentSkills}
        learningPriority={learningPriority}
      />

      {/* Tab Navigation Navigation Bar in Skillaro Neo-Brutalist Style */}
      <div className="flex flex-wrap items-center gap-2 border-b-2 border-ink pb-4">
        <button
          onClick={() => setActiveTab("interview")}
          className={`flex items-center gap-2 px-5 py-3 font-condensed text-base font-bold uppercase tracking-wider transition-transform hover:-translate-y-0.5 ${
            activeTab === "interview"
              ? "hard-shadow bg-lime text-ink"
              : "border-2 border-ink bg-white text-muted hover:text-ink shadow-[2px_2px_0_var(--color-ink)]"
          }`}
        >
          <Mic className="size-4" />
          AI Mock Interview Studio
        </button>

        <button
          onClick={() => setActiveTab("learning")}
          className={`flex items-center gap-2 px-5 py-3 font-condensed text-base font-bold uppercase tracking-wider transition-transform hover:-translate-y-0.5 ${
            activeTab === "learning"
              ? "hard-shadow bg-butter text-ink"
              : "border-2 border-ink bg-white text-muted hover:text-ink shadow-[2px_2px_0_var(--color-ink)]"
          }`}
        >
          <BookOpen className="size-4" />
          Personalized Learning Assistant
        </button>

        <button
          onClick={() => setActiveTab("inspector")}
          className={`flex items-center gap-2 px-5 py-3 font-condensed text-base font-bold uppercase tracking-wider transition-transform hover:-translate-y-0.5 ${
            activeTab === "inspector"
              ? "hard-shadow bg-cyan text-ink"
              : "border-2 border-ink bg-white text-muted hover:text-ink shadow-[2px_2px_0_var(--color-ink)]"
          }`}
        >
          <Activity className="size-4" />
          50% Viva RAG Inspector
        </button>
      </div>

      {/* Active Tab View */}
      <div>
        {activeTab === "interview" && (
          <InterviewStudio
            studentId={studentId}
            studentName={studentName}
            targetRole={targetRole}
            skills={studentSkills}
          />
        )}

        {activeTab === "learning" && (
          <PersonalizedLearningView
            studentId={studentId}
            targetRole={targetRole}
            skills={studentSkills}
            learningPriority={learningPriority}
          />
        )}

        {activeTab === "inspector" && <VivaInspectorView targetRole={targetRole} />}
      </div>
    </div>
  );
}
