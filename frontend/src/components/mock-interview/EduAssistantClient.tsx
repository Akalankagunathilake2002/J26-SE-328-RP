"use client";

import React, { useEffect, useState } from "react";
import PersonalizedLearningView from "./PersonalizedLearningView";
import { ragApi } from "@/lib/ragApi";
import SearchSelect from "./SearchSelect";

interface EduAssistantClientProps {
  studentId: string;
  studentName: string;
}

/** The Edu Assistant on its own page: the student picks the role to learn for (the mock interview sets it
 *  from the interview setup instead). */
export default function EduAssistantClient({ studentId, studentName }: EduAssistantClientProps) {
  const [roles, setRoles] = useState<string[]>([]);
  const [role, setRole] = useState("");

  useEffect(() => {
    ragApi
      .getInterviewRoles()
      .then((r) => setRoles(r.map((x) => x.role)))
      .catch(() => setRoles([]));
  }, []);

  return (
    // mi-type: same typography as the mock interview page, see globals.css
    <div className="mi-type mx-auto max-w-[1440px] space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <label htmlFor="edu-role" className="text-sm font-bold text-ink">
          Learning for
        </label>
        <SearchSelect
          inputId="edu-role"
          className="min-w-64"
          value={role}
          onChange={setRole}
          placeholder="Search roles…"
          options={[{ value: "", label: "All roles" }, ...roles.map((r) => ({ value: r, label: r }))]}
        />
        <span className="text-xs text-muted">Topic suggestions follow the role you pick.</span>
      </div>

      {/* Remounts per role, so the greeting and suggested topics match it */}
      <PersonalizedLearningView
        key={role || "all"}
        studentId={studentId}
        studentName={studentName}
        targetRole={role}
        skills={[]}
        learningPriority=""
      />
    </div>
  );
}
