"use client";

import React, { useEffect, useRef, useState } from "react";
import { FileUp, Loader2, Play, X, Plus, CheckCircle2, AlertCircle, Camera, Sparkles } from "lucide-react";
import { ragApi, type CVProfile, type RoleInfo } from "@/lib/ragApi";

const LEVELS = ["Entry Level", "Mid Level", "Senior Level"];
// Planned length; Elena moves to the closing questions when the time is nearly used
const DURATIONS = [15, 20, 25, 30];

export interface InterviewProfile {
  name: string;
  role: string;
  level: string;
  skills: string[];
  summary: string;
  analysisConsent: boolean;
  durationMinutes: number;
}

interface InterviewSetupProps {
  /** Logged-in user's name, used as the candidate name */
  candidateName: string;
  onStart: (profile: InterviewProfile) => void;
}

export default function InterviewSetup({ candidateName, onStart }: InterviewSetupProps) {
  const [roles, setRoles] = useState<RoleInfo[]>([]);
  const [rolesError, setRolesError] = useState("");
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [analysing, setAnalysing] = useState(false);
  const [cvError, setCvError] = useState("");
  const [profile, setProfile] = useState<CVProfile | null>(null);
  const [skipCv, setSkipCv] = useState(false);
  const [skills, setSkills] = useState<string[]>([]);
  const [newSkill, setNewSkill] = useState("");
  const [role, setRole] = useState("");
  const [level, setLevel] = useState("Entry Level");
  const [duration, setDuration] = useState(25);
  const [consent, setConsent] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInput = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    ragApi
      .getInterviewRoles()
      .then((r) => {
        setRoles(r);
        setRole((cur) => cur || r[0]?.role || "");
      })
      .catch((e) => setRolesError(e instanceof Error ? e.message : "Couldn't load roles"));
  }, []);

  const analyse = async (file: File) => {
    setCvFile(file);
    setCvError("");
    setProfile(null);
    setAnalysing(true);
    try {
      const p = await ragApi.analyzeCV(file);
      setProfile(p);
      setSkills(p.skills);
      if (p.suggested_role && roles.some((r) => r.role === p.suggested_role)) setRole(p.suggested_role);
      if (LEVELS.includes(p.experience_level)) setLevel(p.experience_level);
    } catch (e) {
      setCvError(e instanceof Error ? e.message : "Couldn't read the CV.");
    } finally {
      setAnalysing(false);
    }
  };

  const pick = (files: FileList | null) => {
    const f = files?.[0];
    if (f) analyse(f);
  };

  const addSkill = () => {
    const s = newSkill.trim();
    if (s && !skills.some((x) => x.toLowerCase() === s.toLowerCase())) setSkills([...skills, s]);
    setNewSkill("");
  };

  const roleInfo = roles.find((r) => r.role === role);
  const ready = !!role && (profile || skipCv) && !analysing;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="border-2 border-ink bg-white p-5 sm:p-6 shadow-[5px_5px_0_var(--color-ink)] space-y-1">
        <h2 className="font-display text-2xl uppercase tracking-wide text-ink">Set up your mock interview</h2>
        <p className="text-sm text-muted">
          Upload your CV, choose the role you&apos;re preparing for, then start. Elena tailors her questions to your
          background and level.
        </p>
      </div>

      {/* Step 1: CV */}
      <section className="border-2 border-ink bg-white p-5 sm:p-6 shadow-[5px_5px_0_var(--color-ink)] space-y-4">
        <h3 className="font-condensed text-lg font-bold uppercase tracking-wider text-ink">1 · Upload your CV</h3>
        {!skipCv && (
          <div
            role="button"
            tabIndex={0}
            onClick={() => fileInput.current?.click()}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && fileInput.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); pick(e.dataTransfer.files); }}
            className={`flex cursor-pointer flex-col items-center justify-center gap-2 border-2 border-dashed p-8 text-center transition-colors ${
              dragOver ? "border-brand-blue bg-cyan/20" : "border-ink bg-cream hover:bg-sand/60"
            }`}
          >
            {analysing ? (
              <>
                <Loader2 className="size-7 animate-spin text-ink" />
                <span className="text-sm font-bold text-ink">Reading {cvFile?.name}…</span>
              </>
            ) : (
              <>
                <FileUp className="size-7 text-ink" />
                <span className="text-sm font-bold text-ink">
                  {cvFile ? `Replace ${cvFile.name}` : "Drop your CV here or click to choose"}
                </span>
                <span className="text-xs text-muted">PDF, DOCX or TXT, up to 5 MB · read once, not stored</span>
              </>
            )}
            <input
              ref={fileInput}
              type="file"
              accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
              className="hidden"
              onChange={(e) => { pick(e.target.files); e.target.value = ""; }}
            />
          </div>
        )}

        {cvError && (
          <div className="flex items-start gap-2 border-2 border-ink bg-pink/40 p-3 text-xs font-bold text-ink">
            <AlertCircle className="size-4 shrink-0" /> {cvError}
          </div>
        )}

        {profile && (
          <div className="space-y-3 border-2 border-ink bg-cream p-4">
            <div className="flex flex-wrap items-center gap-2">
              <CheckCircle2 className="size-4 text-emerald-700" />
              <span className="text-sm font-bold text-ink">
                {profile.name ? `${profile.name}'s CV` : "CV"} read ({profile.characters_read.toLocaleString()} characters)
              </span>
              <span className="border border-ink bg-white px-2 py-0.5 text-[11px] font-bold text-muted">
                {profile.method === "llm" ? "Analysed by local AI" : "Keyword match (AI unavailable)"}
              </span>
            </div>
            {profile.summary && <p className="text-sm text-ink">{profile.summary}</p>}
            <div>
              <span className="mb-1.5 block text-xs font-bold uppercase text-muted">Skills (edit if needed)</span>
              <div className="flex flex-wrap gap-2">
                {skills.map((s) => (
                  <span key={s} className="flex items-center gap-1 border border-ink bg-white px-2 py-1 text-xs font-bold text-ink">
                    {s}
                    <button aria-label={`Remove ${s}`} onClick={() => setSkills(skills.filter((x) => x !== s))}>
                      <X className="size-3" />
                    </button>
                  </span>
                ))}
                <span className="flex items-center gap-1 border border-dashed border-ink bg-white px-1">
                  <input
                    value={newSkill}
                    onChange={(e) => setNewSkill(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())}
                    placeholder="Add skill"
                    className="w-24 bg-transparent px-1 py-1 text-xs focus:outline-none"
                  />
                  <button aria-label="Add skill" onClick={addSkill}><Plus className="size-3" /></button>
                </span>
              </div>
            </div>
          </div>
        )}

        {!profile && (
          <button
            onClick={() => setSkipCv(!skipCv)}
            className="text-xs font-bold text-muted underline underline-offset-2 hover:text-ink"
          >
            {skipCv ? "Upload a CV instead" : "Continue without a CV"}
          </button>
        )}
      </section>

      {/* Step 2: role and level */}
      <section className="border-2 border-ink bg-white p-5 sm:p-6 shadow-[5px_5px_0_var(--color-ink)] space-y-4">
        <h3 className="font-condensed text-lg font-bold uppercase tracking-wider text-ink">2 · Choose the job role</h3>
        {rolesError && (
          <div className="flex items-start gap-2 border-2 border-ink bg-pink/40 p-3 text-xs font-bold text-ink">
            <AlertCircle className="size-4 shrink-0" /> {rolesError}
          </div>
        )}
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="space-y-1.5">
            <span className="block text-xs font-bold uppercase text-muted">Job role</span>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full border-2 border-ink bg-white px-3 py-2.5 text-sm font-bold text-ink shadow-[2px_2px_0_var(--color-ink)] focus:outline-none"
            >
              {roles.map((r) => (
                <option key={r.role} value={r.role}>
                  {r.role} ({r.questions} questions){profile?.suggested_role === r.role ? " · suggested" : ""}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1.5">
            <span className="block text-xs font-bold uppercase text-muted">Experience level</span>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className="w-full border-2 border-ink bg-white px-3 py-2.5 text-sm font-bold text-ink shadow-[2px_2px_0_var(--color-ink)] focus:outline-none"
            >
              {LEVELS.map((l) => (
                <option key={l} value={l}>
                  {l}{roleInfo ? ` (${roleInfo.levels[l] ?? 0} questions)` : ""}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1.5">
            <span className="block text-xs font-bold uppercase text-muted">Interview length</span>
            <select
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full border-2 border-ink bg-white px-3 py-2.5 text-sm font-bold text-ink shadow-[2px_2px_0_var(--color-ink)] focus:outline-none"
            >
              {DURATIONS.map((m) => (
                <option key={m} value={m}>
                  About {m} minutes
                </option>
              ))}
            </select>
          </label>
        </div>
        <p className="text-xs text-muted">
          Like a real interview: Elena welcomes you and gets to know you, asks role questions while time allows,
          then gives you a chance to ask her questions before saying goodbye.
        </p>
        {roleInfo && !roleInfo.levels[level] && (
          <p className="text-xs font-bold text-muted">
            No {level} questions for this role yet; Elena will use the closest level available.
          </p>
        )}
      </section>

      {/* Step 3: consent + start */}
      <section className="border-2 border-ink bg-white p-5 sm:p-6 shadow-[5px_5px_0_var(--color-ink)] space-y-4">
        <h3 className="font-condensed text-lg font-bold uppercase tracking-wider text-ink">3 · Delivery feedback (optional)</h3>
        <label className="flex cursor-pointer items-start gap-3">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1 size-4 accent-brand-blue" />
          <span className="text-sm text-ink">
            <span className="flex items-center gap-1.5 font-bold"><Camera className="size-4" /> Analyse my delivery with the camera</span>
            <span className="mt-1 block text-xs text-muted">
              Measures eye contact, smiling, furrowed brows, blinking, head movement and whether your face is in view
              while you answer. It runs only in this browser: no video or images are uploaded or stored, and it does
              not guess your emotions or mood. Speaking pace, pauses and filler words are measured from your answer
              either way.
            </span>
          </span>
        </label>

        <button
          disabled={!ready}
          onClick={() =>
            onStart({
              name: candidateName,
              role,
              level,
              skills,
              summary: profile?.summary || "",
              analysisConsent: consent,
              durationMinutes: duration,
            })
          }
          className="hard-shadow flex w-full items-center justify-center gap-2 bg-lime py-3.5 font-condensed text-base font-bold uppercase tracking-wider text-ink transition-transform hover:-translate-y-0.5 disabled:opacity-50"
        >
          {analysing ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
          Start interview{role ? ` · ${role}` : ""}
        </button>
        {!profile && !skipCv && (
          <p className="flex items-center gap-1.5 text-xs text-muted">
            <Sparkles className="size-3.5" /> Upload your CV first (or continue without one).
          </p>
        )}
      </section>
    </div>
  );
}
