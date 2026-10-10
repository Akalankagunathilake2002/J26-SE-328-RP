"use client";

import React from "react";
import { User, Target, Layers, Compass, Sparkles } from "lucide-react";

interface StudentContextBannerProps {
  studentId: string;
  studentName?: string;
  targetRole: string;
  skills: string[];
  learningPriority: string;
}

export default function StudentContextBanner({
  studentId,
  studentName = "Dilmith",
  targetRole,
  skills,
  learningPriority,
}: StudentContextBannerProps) {
  return (
    <div className="border-2 border-ink bg-cream p-4 sm:p-5 shadow-[4px_4px_0_var(--color-ink)] mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left: Student & Target Career Role */}
        <div className="flex items-start sm:items-center gap-3">
          <div className="grid size-12 shrink-0 place-items-center rounded-full border-2 border-ink bg-sun font-display text-xl font-bold text-ink shadow-[2px_2px_0_var(--color-ink)]">
            {studentName.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-condensed text-lg font-bold uppercase tracking-wider text-ink">
                {studentName}
              </span>
              <span className="border border-ink bg-lime px-2 py-0.5 text-[11px] font-bold font-mono text-ink">
                {studentId}
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted mt-0.5">
              <Target className="size-3.5 text-brand-blue" />
              <span>Target Role:</span>
              <span className="text-ink font-bold underline decoration-brand-blue decoration-2">
                {targetRole}
              </span>
            </div>
          </div>
        </div>

        {/* Middle: Verified Skills */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1 text-xs font-bold uppercase text-muted mr-1">
            <Layers className="size-3.5 text-folder" />
            <span>Profile Skills:</span>
          </div>
          {skills.map((skill) => (
            <span
              key={skill}
              className="border border-ink bg-butter px-2.5 py-1 text-xs font-bold text-ink shadow-[2px_2px_0_var(--color-ink)]"
            >
              {skill}
            </span>
          ))}
        </div>

        {/* Right: Upstream Learning Priority */}
        <div className="border border-ink bg-lavender px-3 py-2 text-xs shadow-[2px_2px_0_var(--color-ink)]">
          <div className="flex items-center gap-1.5 font-bold uppercase text-ink">
            <Sparkles className="size-3.5 text-brand-blue" />
            <span>Priority Skill Gap Focus:</span>
          </div>
          <p className="font-semibold text-ink mt-0.5">{learningPriority}</p>
        </div>
      </div>
    </div>
  );
}
