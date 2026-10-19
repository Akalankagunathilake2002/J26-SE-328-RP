"use client";

import React, { useEffect, useRef, useState } from "react";
import { BookOpen, CheckCircle2, XCircle, RefreshCw, ArrowRight, PenLine, Lightbulb, GraduationCap, AlertTriangle } from "lucide-react";
import SimpleMarkdown from "./SimpleMarkdown";
import { ragApi, type EduLesson, type EduQuiz, type EduGrade, type LessonLevel } from "@/lib/ragApi";

export const LEVELS: { level: LessonLevel; label: string; bloom: string[] }[] = [
  { level: "beginner", label: "Beginner", bloom: ["Remember", "Understand"] },
  { level: "intermediate", label: "Intermediate", bloom: ["Apply", "Analyze"] },
  { level: "advanced", label: "Advanced", bloom: ["Evaluate", "Create"] },
];

export const nextLevel = (level: LessonLevel): LessonLevel | null => {
  const i = LEVELS.findIndex((l) => l.level === level);
  return i < LEVELS.length - 1 ? LEVELS[i + 1].level : null;
};

export const levelLabel = (level: LessonLevel) => LEVELS.find((l) => l.level === level)?.label ?? level;

// Bloom's taxonomy, lowest to highest: one colour per level
const BLOOM_COLOURS: Record<string, string> = {
  Remember: "bg-cyan/40",
  Understand: "bg-lime/60",
  Apply: "bg-butter",
  Analyze: "bg-peach",
  Evaluate: "bg-pink/50",
  Create: "bg-lavender",
};

export function BloomChip({ level }: { level: string }) {
  return (
    <span className={`border border-ink px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-ink ${BLOOM_COLOURS[level] ?? "bg-white"}`}>
      {level}
    </span>
  );
}

export function LessonCard({ lesson }: { lesson: EduLesson }) {
  return (
    <div className="space-y-4 border-2 border-ink bg-white p-5 shadow-[4px_4px_0_var(--color-ink)]">
      <div className="space-y-2 border-b-2 border-ink pb-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="flex items-center gap-1 border border-ink bg-butter px-2 py-0.5 text-[11px] font-bold uppercase text-ink">
            <BookOpen className="size-3" /> {levelLabel(lesson.level)} lesson
          </span>
          {lesson.bloom_levels.map((b) => (
            <BloomChip key={b} level={b} />
          ))}
        </div>
        <h3 className="font-display text-xl uppercase tracking-wide text-ink">{lesson.title}</h3>
        {lesson.introduction && <p className="text-sm text-ink">{lesson.introduction}</p>}
      </div>

      {lesson.sections.map((s, i) => (
        <section key={i} className="space-y-1.5">
          <h4 className="font-condensed text-base font-bold uppercase tracking-wider text-ink">{s.heading}</h4>
          <SimpleMarkdown text={s.body} className="text-sm leading-relaxed text-ink" />
        </section>
      ))}

      {lesson.example && (
        <div className="border-2 border-ink bg-cream p-3 shadow-[2px_2px_0_var(--color-ink)]">
          <span className="mb-1 flex items-center gap-1 font-condensed text-xs font-bold uppercase tracking-wider text-muted">
            <Lightbulb className="size-3.5" /> Example
          </span>
          <SimpleMarkdown text={lesson.example} className="text-sm text-ink" />
        </div>
      )}

      {lesson.key_points.length > 0 && (
        <div className="border border-ink bg-lime/25 p-3">
          <span className="mb-1 block font-condensed text-xs font-bold uppercase tracking-wider text-ink">Key points</span>
          <ul className="list-disc space-y-0.5 pl-5 text-sm text-ink">
            {lesson.key_points.map((k) => (
              <li key={k}>{k}</li>
            ))}
          </ul>
        </div>
      )}

      {lesson.sources.length > 0 && (
        <p className="text-[11px] text-muted">
          From: {lesson.sources.map((s) => s.title).join(" · ")}
        </p>
      )}
    </div>
  );
}

interface QuizCardProps {
  studentId: string;
  targetRole: string;
  topic: string;
  level: LessonLevel;
  keyPoints: string[];
  /** Called once every question has been answered, with the MCQ score */
  onFinished: (correct: number, total: number) => void;
  onContinue: (level: LessonLevel) => void;
  onReview: () => void;
}

export function QuizCard({ studentId, targetRole, topic, level, keyPoints, onFinished, onContinue, onReview }: QuizCardProps) {
  const [quiz, setQuiz] = useState<EduQuiz | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [choices, setChoices] = useState<Record<number, number>>({});
  const [checked, setChecked] = useState(false);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [grades, setGrades] = useState<Record<number, EduGrade | "skipped">>({});
  const [grading, setGrading] = useState<number | null>(null);
  const [gradeError, setGradeError] = useState("");
  const reportedRef = useRef(false);

  const fetchQuiz = () =>
    ragApi
      .eduQuiz({ student_id: studentId, target_role: targetRole, topic, level, key_points: keyPoints })
      .then(setQuiz)
      .catch((e) => setError(e instanceof Error ? e.message : "Skillaro couldn't write the quiz."))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => void fetchQuiz(), []);
  const retry = () => {
    setLoading(true);
    setError("");
    fetchQuiz();
  };

  const correct = quiz ? quiz.mcqs.filter((q, i) => choices[i] === q.answer_index).length : 0;
  const allChosen = !!quiz && quiz.mcqs.every((_, i) => choices[i] != null);
  const opensDone = !!quiz && quiz.open_questions.every((_, i) => grades[i]);
  const finished = !!quiz && (checked || !quiz.mcqs.length) && opensDone;
  const next = nextLevel(level);
  const passed = !quiz?.mcqs.length || correct / quiz.mcqs.length >= 0.6;

  // Reports the stage once: MCQs checked and every written question marked or skipped
  const reportIfDone = (isChecked: boolean, done: Record<number, EduGrade | "skipped">) => {
    if (!quiz || reportedRef.current || !isChecked || !quiz.open_questions.every((_, i) => done[i])) return;
    reportedRef.current = true;
    onFinished(correct, quiz.mcqs.length);
  };
  const setGrade = (i: number, g: EduGrade | "skipped") => {
    const done = { ...grades, [i]: g };
    setGrades(done);
    reportIfDone(checked || !quiz?.mcqs.length, done);
  };

  const grade = async (i: number) => {
    if (!quiz || !answers[i]?.trim()) return;
    const q = quiz.open_questions[i];
    setGrading(i);
    setGradeError("");
    try {
      const g = await ragApi.eduGrade({
        student_id: studentId,
        target_role: targetRole,
        topic,
        level,
        question: q.question,
        bloom_level: q.bloom_level,
        guidance: q.guidance,
        answer: answers[i],
      });
      setGrade(i, g);
    } catch (e) {
      setGradeError(`${e instanceof Error ? e.message : "Marking failed."} Your answer is kept; try again.`);
    } finally {
      setGrading(null);
    }
  };

  if (loading)
    return (
      <div className="flex items-center gap-2 border-2 border-dashed border-ink/50 bg-white p-4 text-sm font-bold text-ink">
        <RefreshCw className="size-4 animate-spin" /> Skillaro is writing your {levelLabel(level).toLowerCase()} check…
      </div>
    );
  if (error || !quiz)
    return (
      <div className="flex flex-wrap items-center gap-3 border-2 border-ink bg-peach p-4 text-sm text-ink">
        <AlertTriangle className="size-4" /> {error}
        <button onClick={retry} className="hard-shadow-sm bg-white px-3 py-1.5 text-xs font-bold uppercase">Try again</button>
      </div>
    );

  return (
    <div className="space-y-4 border-2 border-ink bg-white p-5 shadow-[4px_4px_0_var(--color-ink)]">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b-2 border-ink pb-3">
        <h3 className="flex items-center gap-2 font-condensed text-lg font-bold uppercase tracking-wider text-ink">
          <PenLine className="size-4" /> Check your understanding
        </h3>
        {checked && quiz.mcqs.length > 0 && (
          <span className="border border-ink bg-sun px-2 py-0.5 text-xs font-bold text-ink">
            {correct} / {quiz.mcqs.length} correct
          </span>
        )}
      </div>

      {quiz.mcqs.map((q, i) => (
        <fieldset key={i} className="space-y-2">
          <legend className="flex flex-wrap items-start gap-2 text-sm font-bold text-ink">
            <span>{i + 1}. {q.question}</span> <BloomChip level={q.bloom_level} />
          </legend>
          <div className="grid gap-1.5 sm:grid-cols-2">
            {q.options.map((opt, j) => {
              const chosen = choices[i] === j;
              const right = checked && j === q.answer_index;
              const wrong = checked && chosen && j !== q.answer_index;
              return (
                <label
                  key={j}
                  className={`flex cursor-pointer items-start gap-2 border-2 p-2 text-sm text-ink ${
                    right ? "border-ink bg-lime/60" : wrong ? "border-ink bg-pink/40" : chosen ? "border-ink bg-butter/60" : "border-ink/30 bg-cream"
                  } ${checked ? "cursor-default" : "hover:border-ink"}`}
                >
                  <input
                    type="radio"
                    name={`mcq-${topic}-${level}-${i}`}
                    checked={chosen}
                    disabled={checked}
                    onChange={() => setChoices((c) => ({ ...c, [i]: j }))}
                    className="mt-1 accent-brand-blue"
                  />
                  <span className="flex-1">{opt}</span>
                  {right && <CheckCircle2 className="size-4 shrink-0" />}
                  {wrong && <XCircle className="size-4 shrink-0" />}
                </label>
              );
            })}
          </div>
          {checked && q.explanation && <p className="text-xs text-muted"><b>Why:</b> {q.explanation}</p>}
        </fieldset>
      ))}

      {quiz.mcqs.length > 0 && !checked && (
        <button
          onClick={() => {
            setChecked(true);
            reportIfDone(true, grades);
          }}
          disabled={!allChosen}
          className="hard-shadow flex items-center gap-2 bg-lime px-5 py-2.5 font-condensed text-sm font-bold uppercase tracking-wider text-ink transition-transform hover:-translate-y-0.5 disabled:opacity-50"
        >
          <CheckCircle2 className="size-4" /> Check my answers
        </button>
      )}

      {quiz.open_questions.map((q, k) => {
        const g = grades[k];
        return (
          <div key={k} className="space-y-2 border-t-2 border-ink/20 pt-3">
            <p className="flex flex-wrap items-start gap-2 text-sm font-bold text-ink">
              <span>Written question: {q.question}</span> <BloomChip level={q.bloom_level} />
            </p>
            <textarea
              id={`open-${topic}-${level}-${k}`}
              rows={3}
              value={answers[k] ?? ""}
              disabled={!!g}
              onChange={(e) => setAnswers((a) => ({ ...a, [k]: e.target.value }))}
              placeholder="Write your answer in your own words…"
              className="w-full border-2 border-ink bg-cream p-2.5 text-sm text-ink focus:bg-white focus:outline-none"
            />
            {!g ? (
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => grade(k)}
                  disabled={grading != null || !answers[k]?.trim()}
                  className="hard-shadow-sm flex items-center gap-1.5 bg-butter px-3.5 py-2 text-xs font-bold uppercase text-ink disabled:opacity-50"
                >
                  {grading === k ? <RefreshCw className="size-3.5 animate-spin" /> : <PenLine className="size-3.5" />} Mark my answer
                </button>
                <button
                  onClick={() => setGrade(k, "skipped")}
                  className="border border-ink bg-white px-3 py-2 text-xs font-bold uppercase text-muted hover:text-ink"
                >
                  Skip
                </button>
              </div>
            ) : g === "skipped" ? (
              <p className="text-xs text-muted"><b>What a good answer covers:</b> {q.guidance || "—"}</p>
            ) : (
              <div className="space-y-1.5 border-2 border-ink bg-cream p-3 text-sm text-ink">
                <p className="font-bold">
                  {g.score} / 100 · {{ excellent: "Excellent", good: "Good", partial: "Getting there", needs_work: "Needs more work" }[g.verdict]}
                </p>
                <p>{g.feedback}</p>
                {g.model_answer && (
                  <p className="text-xs text-muted">
                    <b>Model answer:</b> {g.model_answer}
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}
      {gradeError && <p className="text-xs font-bold text-ink">{gradeError}</p>}

      {finished && (
        <div className="flex flex-wrap items-center gap-2 border-t-2 border-ink pt-3">
          {next ? (
            <>
              <p className="w-full text-sm font-bold text-ink">
                {passed
                  ? `Well done! You're ready for the ${levelLabel(next).toLowerCase()} stage.`
                  : "A few to revisit. You can review the lesson or move on when you're ready."}
              </p>
              <button
                onClick={() => onContinue(next)}
                className="hard-shadow flex items-center gap-2 bg-lime px-4 py-2 font-condensed text-sm font-bold uppercase tracking-wider text-ink transition-transform hover:-translate-y-0.5"
              >
                Continue to {levelLabel(next)} <ArrowRight className="size-4" />
              </button>
            </>
          ) : (
            <p className="flex w-full items-center gap-2 text-sm font-bold text-ink">
              <GraduationCap className="size-5" /> You&apos;ve completed all three stages of {topic}, from remembering the basics to designing with it.
            </p>
          )}
          <button
            onClick={onReview}
            className="hard-shadow-sm bg-white px-4 py-2 text-xs font-bold uppercase text-ink transition-transform hover:-translate-y-0.5"
          >
            Review this lesson
          </button>
        </div>
      )}
    </div>
  );
}
