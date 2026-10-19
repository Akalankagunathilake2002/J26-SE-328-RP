"use client";

import React, { useState } from "react";
import { Mic, BookOpen, Activity } from "lucide-react";
import StudentContextBanner from "./StudentContextBanner";
import InterviewStudio from "./InterviewStudio";
import InterviewSetup, { type InterviewProfile } from "./InterviewSetup";
import PersonalizedLearningView from "./PersonalizedLearningView";
import VivaInspectorView from "./VivaInspectorView";
import type { User } from "@/lib/auth";

interface MockInterviewClientProps {
  /** The logged-in user (the page requires a session) */
  user: User;
}

export default function MockInterviewClient({ user }: MockInterviewClientProps) {
  const [activeTab, setActiveTab] = useState<"interview" | "learning" | "inspector">("interview");
  // Set by the interview setup (CV + role + level); null shows the setup screen
  const [profile, setProfile] = useState<InterviewProfile | null>(null);
  const [interviewKey, setInterviewKey] = useState(0);

  // Sessions, answers and learning history are stored against the account id
  const studentId = user.id;
  const studentName = user.full_name || user.email;
  const targetRole = profile?.role || "";
  const studentSkills = profile?.skills ?? [];
  const learningPriority = "Database Connection Management & Scalability";

  const tabClass = (active: boolean, color: string) =>
    `flex items-center gap-2 px-5 py-3 font-condensed text-base font-bold uppercase tracking-wider transition-transform hover:-translate-y-0.5 ${
      active ? `hard-shadow ${color} text-ink` : "border-2 border-ink bg-white text-muted hover:text-ink shadow-[2px_2px_0_var(--color-ink)]"
    }`;

  return (
    <div className="mx-auto max-w-[1440px] space-y-6">
      <StudentContextBanner
        studentId={studentId}
        studentName={studentName}
        targetRole={targetRole}
        skills={studentSkills}
        learningPriority={learningPriority}
      />

      <div className="flex flex-wrap items-center gap-2 border-b-2 border-ink pb-4">
        <button onClick={() => setActiveTab("interview")} className={tabClass(activeTab === "interview", "bg-lime")}>
          <Mic className="size-4" /> AI Mock Interview Studio
        </button>
        <button onClick={() => setActiveTab("learning")} className={tabClass(activeTab === "learning", "bg-butter")}>
          <BookOpen className="size-4" /> Skillaro Edu Assistant
        </button>
        <button onClick={() => setActiveTab("inspector")} className={tabClass(activeTab === "inspector", "bg-cyan")}>
          <Activity className="size-4" /> 50% Viva RAG Inspector
        </button>
      </div>

      <div>
        {activeTab === "interview" &&
          (profile ? (
            <InterviewStudio
              key={interviewKey}
              studentId={studentId}
              profile={profile}
              onExit={() => {
                setProfile(null);
                setInterviewKey((k) => k + 1);
              }}
            />
          ) : (
            <InterviewSetup candidateName={studentName} onStart={setProfile} />
          ))}

        {activeTab === "learning" && (
          <PersonalizedLearningView
            studentId={studentId}
            studentName={studentName}
            targetRole={targetRole}
            skills={studentSkills}
            learningPriority={learningPriority}
          />
        )}

        {activeTab === "inspector" && <VivaInspectorView studentId={studentId} targetRole={targetRole} />}
      </div>
    </div>
  );
}
