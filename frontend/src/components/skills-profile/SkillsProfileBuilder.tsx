"use client";

import { useEffect, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, FileText, Loader2, Sparkles, Trash2, Upload, X } from "lucide-react";

import { ProfileResults } from "./ProfileResults";
import { profileApi, type SkillProfile } from "@/lib/profileApi";

const ACCEPTED = ".pdf,.docx,.txt";
const MAX_FILES = 10;

const BUILD_STEPS = [
  "Reading your documents",
  "Detecting each document's type",
  "Finding skills (dictionary + AI)",
  "Matching skill names",
  "Classifying the evidence",
  "Calculating confidence",
];
// The service builds the profile in one request, so the steps advance on a timer; the last one
// waits for the answer, then every step is ticked before the profile is shown.
const STEP_MS = 900;
const DONE_PAUSE_MS = 700;

interface SkillsProfileBuilderProps {
  userId: string;
  firstName: string;
}

function savedOn(savedAt: string): string {
  return new Date(savedAt).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

// C02: upload evidence, build the evidence-backed skill profile, and show the result
export function SkillsProfileBuilder({ userId, firstName }: SkillsProfileBuilderProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<SkillProfile | null>(null);
  const [loadingSaved, setLoadingSaved] = useState(true);
  const [clearing, setClearing] = useState(false);
  const [step, setStep] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Show the user's saved profile again after a refresh or a new login (TAF task 8)
  useEffect(() => {
    let active = true;
    profileApi
      .getSavedProfile(userId)
      .then((saved) => {
        if (active && saved) setProfile((current) => current ?? saved);
      })
      .catch(() => {
        // No saved profile shown; the user can still build one
      })
      .finally(() => {
        if (active) setLoadingSaved(false);
      });
    return () => {
      active = false;
    };
  }, [userId]);

  // Move the progress on while building; the last step stays active until the service answers
  useEffect(() => {
    if (!building) return;
    const timer = window.setInterval(
      () => setStep((current) => (current >= BUILD_STEPS.length - 1 ? current : current + 1)),
      STEP_MS,
    );
    return () => window.clearInterval(timer);
  }, [building]);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const accepted = Array.from(list).filter((file) => /\.(pdf|docx|txt)$/i.test(file.name));
    setFiles((current) => {
      const names = new Set(current.map((file) => file.name));
      return [...current, ...accepted.filter((file) => !names.has(file.name))].slice(0, MAX_FILES);
    });
    setError(accepted.length < list.length ? "Only PDF, DOCX and TXT files can be added." : null);
  }

  async function build() {
    if (files.length === 0) {
      setError("Add at least one document.");
      return;
    }
    setStep(0);
    setBuilding(true);
    setError(null);
    try {
      const built = await profileApi.buildProfile(files, [], userId);
      setStep(BUILD_STEPS.length);
      await new Promise((resolve) => window.setTimeout(resolve, DONE_PAUSE_MS));
      setProfile(built);
      setFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Building the profile failed.");
    } finally {
      setBuilding(false);
    }
  }

  // Delete the saved profile (also from the database) so the user can start again
  async function clear() {
    if (!window.confirm("Clear your skill profile? It will also be deleted from your account.")) return;
    setClearing(true);
    setError(null);
    try {
      await profileApi.clearProfile(userId);
      setProfile(null);
      setFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clearing the profile failed.");
    } finally {
      setClearing(false);
    }
  }

  return (
    <div className="space-y-6">
      <section>
        <p className="inline-block border-2 border-ink bg-pink px-3 py-0.5 font-condensed text-[17px] font-semibold uppercase">
          Hi {firstName}
        </p>
        <h1 className="mt-3 text-3xl font-black sm:text-4xl">Skills Profile</h1>
        <p className="mt-2 max-w-[620px] text-[15px] text-muted">
          Upload your CV, project or internship reports, certificates and transcripts.
          Each skill gets a confidence score based on how much independent proof supports it.
        </p>
      </section>

      <section className="rounded-2xl border-2 border-ink bg-white p-5 shadow-[4px_4px_0px_#000] sm:p-6">
        <div className="mb-4 flex items-center gap-2">
          <Upload className="size-5" />
          <h2 className="text-lg font-extrabold sm:text-xl">Add evidence</h2>
        </div>

        <div className="grid gap-5 md:grid-cols-[1.3fr_1fr]">
          <div>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                addFiles(event.dataTransfer.files);
              }}
              className={`flex w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-ink px-4 py-8 text-center transition-colors ${
                dragging ? "bg-lime" : "bg-page hover:bg-cream"
              }`}
            >
              <span className="grid size-11 place-items-center rounded-full border-2 border-ink bg-white shadow-[2px_2px_0px_#000]">
                <Upload className="size-5" />
              </span>
              <span className="mt-3 font-bold">Drag &amp; drop files here, or click to choose</span>
              <span className="mt-1 text-xs text-muted">PDF, DOCX or TXT · up to {MAX_FILES} files · 10 MB each</span>
            </button>
            <input
              ref={inputRef}
              id="profile-files"
              type="file"
              accept={ACCEPTED}
              multiple
              className="hidden"
              onChange={(event) => {
                addFiles(event.target.files);
                event.target.value = "";
              }}
            />

            {files.length > 0 && (
              <ul className="mt-4 space-y-2">
                {files.map((file) => (
                  <li
                    key={file.name}
                    className="flex items-center justify-between gap-3 rounded-lg border-2 border-ink bg-cream px-3 py-2 text-sm"
                  >
                    <span className="flex min-w-0 items-center gap-2">
                      <FileText className="size-4 shrink-0" />
                      <span className="truncate font-semibold">{file.name}</span>
                    </span>
                    <button
                      type="button"
                      aria-label={`Remove ${file.name}`}
                      onClick={() => setFiles((current) => current.filter((f) => f.name !== file.name))}
                      className="rounded p-0.5 hover:bg-pink"
                    >
                      <X className="size-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="flex flex-col gap-4">
            {/* GitHub links are supported by the service; the input returns to the page after PP1. */}
            <div className="rounded-xl border-2 border-ink bg-lavender p-3 text-[13px] leading-relaxed">
              <p className="font-bold">You don&apos;t choose a document type.</p>
              <p className="mt-1">
                The system reads each file and decides whether it is a CV, certificate, project report or academic
                document, so evidence can&apos;t be mislabelled.
              </p>
            </div>

            <button
              type="button"
              onClick={build}
              disabled={building}
              className="mt-auto inline-flex h-12 items-center justify-center gap-2 rounded-xl border-2 border-ink bg-sun font-extrabold shadow-[4px_4px_0px_#000] transition-transform hover:-translate-y-0.5 disabled:cursor-wait disabled:opacity-70"
            >
              {building ? <Loader2 className="size-5 animate-spin" /> : <Sparkles className="size-5" />}
              {building ? "Building your profile…" : "Build my profile"}
            </button>
          </div>
        </div>

        {error && (
          <p className="mt-4 flex items-center gap-2 rounded-lg border-2 border-ink bg-[#ffe1e1] px-3 py-2 text-sm font-semibold">
            <AlertCircle className="size-4 shrink-0" /> {error}
          </p>
        )}

        {building && (
          <div className="mt-5 rounded-2xl border-2 border-ink bg-cream p-4 sm:p-5" role="status" aria-live="polite">
            <div className="flex items-center justify-between gap-3">
              <p className="font-extrabold">
                {step >= BUILD_STEPS.length ? "Done! Showing your profile…" : "Building your profile…"}
              </p>
              <span className="font-condensed text-xl font-bold">
                {Math.round((Math.max(step, 0.4) / BUILD_STEPS.length) * 100)}%
              </span>
            </div>
            <div className="mt-2 h-4 overflow-hidden rounded-full border-2 border-ink bg-white">
              <div
                className="h-full rounded-full bg-lime transition-[width] duration-700 ease-out"
                style={{ width: `${(Math.max(step, 0.4) / BUILD_STEPS.length) * 100}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-muted">
              {step >= BUILD_STEPS.length
                ? `All ${BUILD_STEPS.length} steps finished.`
                : `Step ${step + 1} of ${BUILD_STEPS.length}: ${BUILD_STEPS[step]}. The first run can take a minute or two.`}
            </p>

            <ol className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
              {BUILD_STEPS.map((label, index) => {
                const done = index < step;
                const active = index === step;
                return (
                  <li
                    key={label}
                    className={`flex items-center gap-2.5 rounded-xl border-2 px-3 py-2 transition-colors ${
                      done
                        ? "border-ink bg-lime/60"
                        : active
                          ? "border-ink bg-white shadow-[2px_2px_0px_#000]"
                          : "border-dashed border-ink/40 text-muted"
                    }`}
                  >
                    <span
                      className={`grid size-6 shrink-0 place-items-center rounded-full border-2 text-[11px] font-bold ${
                        done ? "border-ink bg-lime" : active ? "border-ink bg-sun" : "border-ink/40 bg-white"
                      }`}
                    >
                      {done ? (
                        <CheckCircle2 className="size-4" />
                      ) : active ? (
                        <Loader2 className="size-3.5 animate-spin" />
                      ) : (
                        index + 1
                      )}
                    </span>
                    <span className={active ? "font-bold" : ""}>{label}</span>
                  </li>
                );
              })}
            </ol>
          </div>
        )}
      </section>

      {loadingSaved && !profile && (
        <p className="flex items-center gap-2 text-sm font-semibold text-muted">
          <Loader2 className="size-4 animate-spin" /> Loading your saved profile…
        </p>
      )}

      {profile && !building && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <p
            className={`flex flex-1 items-center gap-2 rounded-2xl border-2 border-ink px-4 py-2 text-sm font-semibold ${
              profile.saved_at ? "bg-lime" : "bg-[#ffe1e1]"
            }`}
          >
            {profile.saved_at ? <CheckCircle2 className="size-4 shrink-0" /> : <AlertCircle className="size-4 shrink-0" />}
            {profile.saved_at
              ? `Saved to your account on ${savedOn(profile.saved_at)}. Add evidence and build again to update it.`
              : "This profile could not be saved, so it will be gone after a refresh."}
          </p>
          <button
            type="button"
            onClick={clear}
            disabled={clearing}
            className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-full border-2 border-ink bg-white px-4 text-sm font-bold shadow-[3px_3px_0px_#000] transition-transform hover:-translate-y-0.5 hover:bg-[#ffe1e1] disabled:cursor-wait disabled:opacity-70"
          >
            {clearing ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
            Clear profile
          </button>
        </div>
      )}

      {profile && <ProfileResults profile={profile} />}
    </div>
  );
}
