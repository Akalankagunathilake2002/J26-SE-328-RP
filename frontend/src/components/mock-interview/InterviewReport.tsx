"use client";

import React from "react";
import { Award, RotateCcw, CheckCircle2, AlertCircle, Eye, Smile, Gauge, MessageSquare } from "lucide-react";
import type { DeliveryTelemetry, InterviewReport as Report } from "@/lib/ragApi";

interface InterviewReportProps {
  report: Report;
  role: string;
  level: string;
  /** Delivery cues measured in the browser for each answered turn */
  delivery: Record<string, DeliveryTelemetry>;
  onRestart: () => void;
}

const pct = (x?: number | null) => (x == null ? "–" : `${Math.round(x * 100)}%`);
const mean = (xs: (number | undefined | null)[]) => {
  const v = xs.filter((x): x is number => typeof x === "number");
  return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
};

function Score({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="border-2 border-ink bg-cream p-2.5 text-center shadow-[2px_2px_0_var(--color-ink)]">
      <span className="block text-[10px] font-bold uppercase text-muted">{label}</span>
      <span className="font-display text-2xl font-bold text-ink">{value == null ? "–" : value.toFixed(1)}</span>
      <span className="block text-[10px] font-bold text-muted">/ 5.0</span>
    </div>
  );
}

function DeliveryRow({ d }: { d?: DeliveryTelemetry }) {
  if (!d) return null;
  const items = [
    d.words_per_minute != null && `${Math.round(d.words_per_minute)} wpm`,
    d.filler_words_count != null && `${d.filler_words_count} fillers`,
    d.pause_ratio != null && `${pct(d.pause_ratio)} pauses`,
    d.eye_contact_ratio != null && `${pct(d.eye_contact_ratio)} eye contact`,
    d.smile_ratio != null && `${pct(d.smile_ratio)} smiling`,
    d.head_steadiness != null && `steadiness ${pct(d.head_steadiness)}`,
    d.face_visible_ratio != null && d.face_visible_ratio < 0.95 && `face in view ${pct(d.face_visible_ratio)}`,
  ].filter(Boolean) as string[];
  if (!items.length) return null;
  return <p className="text-[11px] font-semibold text-muted">Delivery: {items.join(" · ")}</p>;
}

export default function InterviewReport({ report, role, level, delivery, onRestart }: InterviewReportProps) {
  const answered = report.turns.filter((t) => t.evaluated);
  const all = Object.values(delivery);
  const avg = {
    eye: mean(all.map((d) => d.eye_contact_ratio)),
    smile: mean(all.map((d) => d.smile_ratio)),
    steady: mean(all.map((d) => d.head_steadiness)),
    wpm: mean(all.map((d) => d.words_per_minute)),
    pauses: mean(all.map((d) => d.pause_ratio)),
    fillers: mean(all.map((d) => d.filler_words_count)),
  };
  const hasCamera = avg.eye != null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 border-2 border-ink bg-white p-5 shadow-[5px_5px_0_var(--color-ink)] sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-display text-2xl uppercase tracking-wide text-ink flex items-center gap-2">
            <Award className="size-6 text-brand-blue" /> Interview report
          </h2>
          <p className="text-sm text-muted">
            {role} · {level} · {report.turns_completed} of {report.questions_asked} questions answered
          </p>
        </div>
        <button
          onClick={onRestart}
          className="hard-shadow flex items-center gap-2 bg-lime px-5 py-3 font-condensed text-base font-bold uppercase tracking-wider text-ink transition-transform hover:-translate-y-0.5"
        >
          <RotateCcw className="size-4" /> New interview
        </button>
      </div>

      {answered.length === 0 ? (
        <div className="border-2 border-ink bg-white p-6 text-sm text-muted shadow-[5px_5px_0_var(--color-ink)]">
          No answers were evaluated in this interview, so there are no scores to show.
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="border-2 border-ink bg-white p-5 shadow-[5px_5px_0_var(--color-ink)] space-y-3">
            <h3 className="font-condensed text-lg font-bold uppercase tracking-wider text-ink">Average scores</h3>
            <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
              <Score label="Knowledge" value={report.overall_scores.technical_accuracy} />
              <Score label="Relevance" value={report.overall_scores.relevance} />
              <Score label="Explanation" value={report.overall_scores.explanation_quality} />
              <Score label="Clarity" value={report.overall_scores.clarity} />
            </div>
          </section>

          <section className="border-2 border-ink bg-white p-5 shadow-[5px_5px_0_var(--color-ink)] space-y-3">
            <h3 className="font-condensed text-lg font-bold uppercase tracking-wider text-ink">Delivery</h3>
            <div className="grid grid-cols-2 gap-2.5 text-sm">
              <span className="flex items-center gap-2"><MessageSquare className="size-4" /> Pace: <b>{avg.wpm == null ? "–" : `${Math.round(avg.wpm)} wpm`}</b></span>
              <span className="flex items-center gap-2"><Gauge className="size-4" /> Pauses: <b>{pct(avg.pauses)}</b></span>
              <span className="flex items-center gap-2"><MessageSquare className="size-4" /> Fillers: <b>{avg.fillers == null ? "–" : avg.fillers.toFixed(1)}</b> per answer</span>
              {hasCamera ? (
                <>
                  <span className="flex items-center gap-2"><Eye className="size-4" /> Eye contact: <b>{pct(avg.eye)}</b></span>
                  <span className="flex items-center gap-2"><Smile className="size-4" /> Smiling: <b>{pct(avg.smile)}</b></span>
                  <span className="flex items-center gap-2"><Gauge className="size-4" /> Head steadiness: <b>{pct(avg.steady)}</b></span>
                </>
              ) : (
                <span className="col-span-2 text-xs text-muted">Camera delivery analysis was off for this interview.</span>
              )}
            </div>
            <p className="text-[11px] text-muted">
              Measured from observable cues only (where you looked, smiling, head movement, pace, pauses). It doesn&apos;t
              judge emotions or mood.
            </p>
          </section>
        </div>
      )}

      <section className="space-y-4">
        {report.turns.map((t, i) => (
          <div key={t.turn_id} className="border-2 border-ink bg-white p-5 shadow-[4px_4px_0_var(--color-ink)] space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="border border-ink bg-sun px-2.5 py-1 text-xs font-bold text-ink">
                Question {i + 1} · {t.topic}
              </span>
              {t.evaluated ? (
                <span className="text-xs font-bold text-ink">
                  {[t.technical_accuracy, t.relevance, t.explanation_quality, t.clarity].map((s) => s?.toFixed(1)).join(" / ")}
                </span>
              ) : (
                <span className="text-xs font-bold text-muted">Not answered</span>
              )}
            </div>
            <p className="text-sm font-bold text-ink">{t.question}</p>
            {t.transcript && <p className="text-xs italic text-muted">&ldquo;{t.transcript}&rdquo;</p>}
            <DeliveryRow d={delivery[t.turn_id]} />
            {t.evaluated && (
              <div className="grid gap-3 sm:grid-cols-2">
                {t.strengths.length > 0 && (
                  <ul className="space-y-1 text-xs text-ink">
                    {t.strengths.slice(0, 3).map((s) => (
                      <li key={s} className="flex gap-1.5"><CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-emerald-700" />{s}</li>
                    ))}
                  </ul>
                )}
                {t.missing_concepts.length > 0 && (
                  <ul className="space-y-1 text-xs text-ink">
                    {t.missing_concepts.slice(0, 3).map((s) => (
                      <li key={s} className="flex gap-1.5"><AlertCircle className="mt-0.5 size-3.5 shrink-0 text-pink" />{s}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        ))}
      </section>
    </div>
  );
}
