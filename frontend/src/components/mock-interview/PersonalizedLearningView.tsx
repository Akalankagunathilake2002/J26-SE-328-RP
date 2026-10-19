"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Send, RefreshCw, Sparkles, GraduationCap, AlertTriangle, Bookmark, CheckCircle2, BookOpen } from "lucide-react";
import SimpleMarkdown from "./SimpleMarkdown";
import { LessonCard, QuizCard, BloomChip, LEVELS, levelLabel } from "./SkillaroLesson";
import { ragApi, type EduChatMessage, type EduLesson, type LessonLevel, type LearningTopic, type SourceCitation } from "@/lib/ragApi";

interface PersonalizedLearningViewProps {
  studentId: string;
  studentName: string;
  targetRole: string;
  skills: string[];
  learningPriority: string;
}

type ChatItem =
  | { id: number; kind: "text"; role: "user" | "assistant"; content: string; suggested?: string[]; sources?: SourceCitation[] }
  | { id: number; kind: "lesson"; lesson: EduLesson }
  | { id: number; kind: "quiz"; topic: string; level: LessonLevel; keyPoints: string[] }
  | { id: number; kind: "error"; content: string; retry: () => void };

// A chat item before it gets its id (Omit applied to each member of the union)
type NewChatItem = ChatItem extends infer T ? (T extends ChatItem ? Omit<T, "id"> : never) : never;

const SUGGESTIONS = 6;
const HISTORY = 8; // chat messages sent with each turn

export default function PersonalizedLearningView({
  studentId,
  studentName,
  targetRole,
  skills,
  learningPriority,
}: PersonalizedLearningViewProps) {
  const [topics, setTopics] = useState<LearningTopic[]>([]);
  const [items, setItems] = useState<ChatItem[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState<"" | "chat" | "lesson">("");
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  const [activeLevel, setActiveLevel] = useState<LessonLevel>("beginner");
  // Stages finished per topic, with the MCQ score
  const [progress, setProgress] = useState<Record<string, Partial<Record<LessonLevel, string>>>>({});
  const nextId = useRef(1);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const firstName = studentName && !studentName.includes("@") ? studentName.split(" ")[0] : "";
  const roleLabel = targetRole || "your career";

  useEffect(() => {
    let cancelled = false;
    ragApi
      .getLearningTopics(targetRole)
      .then((t) => !cancelled && setTopics(t))
      .catch(() => !cancelled && setTopics([]));
    return () => {
      cancelled = true;
    };
  }, [targetRole]);

  // Distinct curriculum topics: the learning priority first, then ones matching the student's skills,
  // then the best-covered (most documents)
  const suggestedTopics = useMemo(() => {
    const counts = new Map<string, { n: number; text: string }>();
    for (const t of topics) {
      const c = counts.get(t.topic) ?? { n: 0, text: t.topic };
      counts.set(t.topic, { n: c.n + 1, text: `${c.text} ${t.title}` });
    }
    const lowered = skills.map((s) => s.toLowerCase());
    const priorityWords = learningPriority.toLowerCase().split(/\W+/).filter((w) => w.length > 3);
    const score = (topic: string) => {
      const text = counts.get(topic)!.text.toLowerCase();
      return (
        (priorityWords.some((w) => text.includes(w)) ? 1000 : 0) +
        (lowered.some((s) => text.includes(s)) ? 500 : 0) +
        counts.get(topic)!.n
      );
    };
    return [...counts.keys()].sort((a, b) => score(b) - score(a));
  }, [topics, skills, learningPriority]);

  const push = (item: NewChatItem) => setItems((xs) => [...xs, { ...item, id: nextId.current++ } as ChatItem]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [items, busy]);

  // ---------------------------------------------------------------- chat
  const send = async (text: string = input) => {
    const message = text.trim();
    if (!message || busy) return;
    const history: EduChatMessage[] = items
      .filter((x): x is Extract<ChatItem, { kind: "text" }> => x.kind === "text")
      .slice(-HISTORY)
      .map((x) => ({ role: x.role, content: x.content }));
    push({ kind: "text", role: "user", content: message });
    setInput("");
    setBusy("chat");
    try {
      const res = await ragApi.eduChat({
        student_id: studentId,
        target_role: targetRole,
        current_skills: skills,
        learning_priority: learningPriority,
        student_name: studentName,
        message,
        history,
        current_topic: activeTopic ?? undefined,
      });
      push({ kind: "text", role: "assistant", content: res.reply, suggested: res.suggested_topics, sources: res.sources });
    } catch (e) {
      push({
        kind: "error",
        content: `${e instanceof Error ? e.message : "Skillaro didn't respond."} Check that the learning service and the local LLM are running.`,
        retry: () => send(message),
      });
    } finally {
      setBusy("");
    }
  };

  // ---------------------------------------------------------------- lessons
  const teach = async (topic: string, level: LessonLevel = "beginner") => {
    if (busy) return;
    setActiveTopic(topic);
    setActiveLevel(level);
    push({ kind: "text", role: "user", content: `Teach me ${topic} (${levelLabel(level).toLowerCase()})` });
    setBusy("lesson");
    try {
      const lesson = await ragApi.eduLesson({ student_id: studentId, target_role: targetRole, current_skills: skills, topic, level });
      push({ kind: "lesson", lesson });
      push({ kind: "quiz", topic, level, keyPoints: lesson.key_points });
    } catch (e) {
      push({
        kind: "error",
        content: `${e instanceof Error ? e.message : "Skillaro couldn't prepare the lesson."}`,
        retry: () => teach(topic, level),
      });
    } finally {
      setBusy("");
    }
  };

  const markFinished = useCallback((topic: string, level: LessonLevel, correct: number, total: number) => {
    setProgress((p) => ({ ...p, [topic]: { ...p[topic], [level]: total ? `${correct}/${total}` : "done" } }));
  }, []);

  const review = (topic: string, level: LessonLevel) => {
    const idx = items.findLastIndex((x) => x.kind === "lesson" && x.lesson.topic === topic && x.lesson.level === level);
    if (idx < 0) return;
    document.getElementById(`chat-item-${items[idx].id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const topicChips = (list: string[]) => (
    <div className="flex flex-wrap gap-2">
      {list.map((t) => (
        <button
          key={t}
          onClick={() => teach(t)}
          disabled={!!busy}
          className="flex items-center gap-1.5 border border-ink bg-sand px-3 py-1.5 text-left text-xs font-bold text-ink shadow-[2px_2px_0_var(--color-ink)] transition-colors hover:bg-butter disabled:opacity-50"
        >
          <GraduationCap className="size-3.5" /> Teach me {t}
        </button>
      ))}
    </div>
  );

  const bubble = (role: "user" | "assistant", children: React.ReactNode) => (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] border-2 border-ink p-3 text-sm text-ink shadow-[2px_2px_0_var(--color-ink)] ${
          role === "user" ? "bg-lime/50" : "bg-white"
        }`}
      >
        {children}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-2 border-ink bg-white p-4 shadow-[4px_4px_0_var(--color-ink)]">
        <div className="flex flex-wrap items-center gap-2">
          <span className="border border-ink bg-butter px-2 py-0.5 font-condensed text-xs font-bold uppercase tracking-wider text-ink">
            Learning
          </span>
          <span className="border border-ink bg-lime px-2 py-0.5 text-xs font-bold text-ink">{targetRole || "All roles"}</span>
        </div>
        <h2 className="mt-1 font-display text-2xl uppercase tracking-wide text-ink">Skillaro Edu Assistant</h2>
        <p className="text-xs text-muted">
          Chat with Skillaro about anything in your curriculum, or learn a topic step by step from beginner to advanced, with
          quizzes built on Bloom&apos;s taxonomy. Answers are grounded in the course material, with sources.
        </p>
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        {/* Chat */}
        <div className="flex min-w-0 flex-col border-2 border-ink bg-cream shadow-[5px_5px_0_var(--color-ink)]">
          <div ref={scrollRef} className="h-[62vh] min-h-[420px] space-y-4 overflow-y-auto p-4" aria-live="polite">
            {bubble(
              "assistant",
              <div className="space-y-3">
                <p>
                  Hi{firstName ? ` ${firstName}` : ""}! I&apos;m <b>Skillaro</b>, your Edu Assistant. Ask me anything about {roleLabel}{" "}
                  topics, or pick a topic and I&apos;ll teach it to you step by step: first the basics, then how to use it, then how
                  experts make decisions with it. Each step ends with a short quiz.
                </p>
                {suggestedTopics.length > 0 ? (
                  <>
                    <p className="text-xs font-bold uppercase text-muted">Topics I&apos;d suggest for you:</p>
                    {topicChips(suggestedTopics.slice(0, SUGGESTIONS))}
                  </>
                ) : (
                  <p className="text-xs text-muted">Loading topics from your curriculum…</p>
                )}
              </div>
            )}

            {items.map((item) => (
              <div key={item.id} id={`chat-item-${item.id}`} className="scroll-mt-4">
                {item.kind === "text" &&
                  bubble(
                    item.role,
                    item.role === "user" ? (
                      <p className="whitespace-pre-line">{item.content}</p>
                    ) : (
                      <div className="space-y-3">
                        <SimpleMarkdown text={item.content} className="leading-relaxed" />
                        {item.suggested && item.suggested.length > 0 && topicChips(item.suggested)}
                        {item.sources && item.sources.length > 0 && (
                          <p className="flex items-start gap-1 text-[11px] text-muted">
                            <Bookmark className="mt-0.5 size-3 shrink-0" />
                            {item.sources.map((s) => s.title).join(" · ")}
                          </p>
                        )}
                      </div>
                    )
                  )}
                {item.kind === "lesson" && <LessonCard lesson={item.lesson} />}
                {item.kind === "quiz" && (
                  <QuizCard
                    studentId={studentId}
                    targetRole={targetRole}
                    topic={item.topic}
                    level={item.level}
                    keyPoints={item.keyPoints}
                    onFinished={(c, t) => markFinished(item.topic, item.level, c, t)}
                    onContinue={(lvl) => teach(item.topic, lvl)}
                    onReview={() => review(item.topic, item.level)}
                  />
                )}
                {item.kind === "error" && (
                  <div className="flex flex-wrap items-center gap-3 border-2 border-ink bg-peach p-3 text-sm text-ink">
                    <AlertTriangle className="size-4 shrink-0" /> <span className="flex-1">{item.content}</span>
                    <button onClick={item.retry} disabled={!!busy} className="hard-shadow-sm bg-white px-3 py-1.5 text-xs font-bold uppercase disabled:opacity-50">
                      Try again
                    </button>
                  </div>
                )}
              </div>
            ))}

            {busy &&
              bubble(
                "assistant",
                <p className="flex items-center gap-2 text-muted">
                  <RefreshCw className="size-4 animate-spin" />
                  {busy === "lesson" ? "Skillaro is preparing your lesson… (this can take up to a minute)" : "Skillaro is typing…"}
                </p>
              )}
          </div>

          <div className="flex gap-2 border-t-2 border-ink bg-white p-3">
            <label htmlFor="skillaro-input" className="sr-only">
              Message Skillaro
            </label>
            <textarea
              id="skillaro-input"
              ref={inputRef}
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder={activeTopic ? `Ask about ${activeTopic}, or anything else…` : "Ask Skillaro anything, e.g. how does connection pooling work?"}
              className="flex-1 resize-none border-2 border-ink bg-cream p-2.5 text-sm text-ink focus:bg-white focus:outline-none"
            />
            <button
              onClick={() => send()}
              disabled={!!busy || !input.trim()}
              className="hard-shadow flex items-center gap-2 self-end bg-lime px-4 py-2.5 font-condensed text-sm font-bold uppercase tracking-wider text-ink transition-transform hover:-translate-y-0.5 disabled:opacity-50"
            >
              <Send className="size-4" /> Send
            </button>
          </div>
        </div>

        {/* Learning path */}
        <aside className="space-y-4">
          <div className="space-y-3 border-2 border-ink bg-white p-4 shadow-[4px_4px_0_var(--color-ink)]">
            <h3 className="flex items-center gap-2 font-condensed text-base font-bold uppercase tracking-wider text-ink">
              <Sparkles className="size-4" /> Learning path
            </h3>
            {activeTopic ? (
              <>
                <p className="text-sm font-bold text-ink">{activeTopic}</p>
                <ol className="space-y-2">
                  {LEVELS.map((l) => {
                    const done = progress[activeTopic]?.[l.level];
                    const current = l.level === activeLevel;
                    return (
                      <li
                        key={l.level}
                        className={`space-y-1 border-2 p-2 ${current ? "border-ink bg-butter/50" : "border-ink/30 bg-cream"}`}
                      >
                        <div className="flex items-center justify-between gap-2 text-sm font-bold text-ink">
                          <span>{l.label}</span>
                          {done ? (
                            <span className="flex items-center gap-1 text-xs"><CheckCircle2 className="size-3.5" /> {done}</span>
                          ) : (
                            <button
                              onClick={() => teach(activeTopic, l.level)}
                              disabled={!!busy}
                              className="text-xs font-bold text-brand-blue underline disabled:opacity-50"
                            >
                              {current ? "Restart" : "Start"}
                            </button>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {l.bloom.map((b) => (
                            <BloomChip key={b} level={b} />
                          ))}
                        </div>
                      </li>
                    );
                  })}
                </ol>
              </>
            ) : (
              <p className="text-xs text-muted">Pick a topic to start. Each topic has three stages, each covering two levels of Bloom&apos;s taxonomy.</p>
            )}
          </div>

          {suggestedTopics.length > SUGGESTIONS && (
            <div className="space-y-2 border-2 border-ink bg-white p-4 shadow-[4px_4px_0_var(--color-ink)]">
              <label htmlFor="skillaro-topic" className="flex items-center gap-2 font-condensed text-base font-bold uppercase tracking-wider text-ink">
                <BookOpen className="size-4" /> All topics ({suggestedTopics.length})
              </label>
              <select
                id="skillaro-topic"
                value=""
                onChange={(e) => e.target.value && teach(e.target.value)}
                disabled={!!busy}
                className="w-full border-2 border-ink bg-white px-2 py-2 text-sm font-bold text-ink focus:outline-none"
              >
                <option value="">Choose a topic to learn…</option>
                {suggestedTopics.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="space-y-2 border border-ink bg-lavender/60 p-3 text-xs text-ink">
            <p className="font-bold">How the stages follow Bloom&apos;s taxonomy</p>
            <p><b>Beginner:</b> remember the terms and understand the idea.</p>
            <p><b>Intermediate:</b> apply it to real tasks and analyse situations.</p>
            <p><b>Advanced:</b> evaluate trade-offs and create your own designs.</p>
          </div>
        </aside>
      </div>
    </div>
  );
}
