"use client";

import { BookOpen, Check, FlaskConical, Layers, Lightbulb, Mic, Sparkles, Video, Webhook, Workflow, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState, type MouseEvent, type ReactNode, type RefObject } from "react";

import { ArrowRightIcon } from "@/components/icons";

import { Reveal } from "./Reveal";

/* ───────────────────────── shared helpers ───────────────────────── */

/** True while the element is on screen. */
function useInView(ref: RefObject<HTMLElement | null>, threshold = 0.35) {
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => setInView(entry.isIntersecting), { threshold });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref, threshold]);
  return inView;
}

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    query.addEventListener("change", update);
    const frame = requestAnimationFrame(update);
    return () => {
      query.removeEventListener("change", update);
      cancelAnimationFrame(frame);
    };
  }, []);
  return reduced;
}

/** Card with a soft glow that follows the mouse (a common pattern on modern product sites). */
function SpotlightCard({ className, glow, children }: { className: string; glow: string; children: ReactNode }) {
  const onMove = (event: MouseEvent<HTMLDivElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    event.currentTarget.style.setProperty("--x", `${event.clientX - box.left}px`);
    event.currentTarget.style.setProperty("--y", `${event.clientY - box.top}px`);
  };
  return (
    <div onMouseMove={onMove} className={`group relative overflow-hidden ${className}`}>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{ background: `radial-gradient(420px circle at var(--x, 50%) var(--y, 50%), ${glow}, transparent 45%)` }}
      />
      <div className="relative z-10 h-full">{children}</div>
    </div>
  );
}

/* ───────────────────────── learning path ───────────────────────── */

type Course = {
  gap: string;
  title: string;
  lessons: number;
  topics: string[];
  mastery: number;
  status: string;
  icon: LucideIcon;
  tone: { card: string; icon: string; bar: string; chip: string; glow: string };
};

/** An example plan built from the gaps in the example readiness report above. */
const courses: Course[] = [
  {
    gap: "REST APIs",
    title: "Design and use REST APIs",
    lessons: 6,
    topics: ["HTTP methods and status codes", "Designing clean endpoints", "Testing APIs with Postman"],
    mastery: 65,
    status: "In progress",
    icon: Webhook,
    tone: { card: "bg-[#f4f0ff] ring-[#e4dcff]", icon: "bg-[#6d4aff] text-white", bar: "bg-[#6d4aff]", chip: "bg-[#6d4aff] text-white", glow: "rgba(109,74,255,0.16)" },
  },
  {
    gap: "CI/CD",
    title: "Automate builds and deploys",
    lessons: 5,
    topics: ["Git branching workflows", "GitHub Actions basics", "Running tests in the pipeline"],
    mastery: 30,
    status: "Up next",
    icon: Workflow,
    tone: { card: "bg-[#eef6ff] ring-[#d3e6fb]", icon: "bg-[#006ee9] text-white", bar: "bg-[#006ee9]", chip: "bg-[#dbeeff] text-[#0b4a80]", glow: "rgba(0,110,233,0.14)" },
  },
  {
    gap: "Testing",
    title: "Write tests that catch bugs",
    lessons: 5,
    topics: ["Unit tests", "Integration tests", "Test-driven development"],
    mastery: 0,
    status: "Then",
    icon: FlaskConical,
    tone: { card: "bg-[#fff1f6] ring-[#fbd7e6]", icon: "bg-[#d6336c] text-white", bar: "bg-[#d6336c]", chip: "bg-[#ffdcee] text-[#7a1048]", glow: "rgba(214,51,108,0.14)" },
  },
];

function LearningPath() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, 0.25);

  return (
    <div ref={ref} className="rounded-[28px] border border-[#ece8f7] bg-white/80 p-5 shadow-[0_30px_60px_-40px_rgba(74,47,208,0.5)] backdrop-blur-sm sm:p-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="inline-flex items-center gap-2 text-[13px] font-extrabold uppercase tracking-[0.08em] text-[#4a2fd0]">
            <Sparkles className="size-4" aria-hidden="true" /> Your learning path
          </p>
          <h3 className="mt-1 font-editorial text-[26px] font-semibold leading-tight">Courses built from your skill gaps.</h3>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[13px] font-bold">
          <span className="text-[#8a877f]">Your gaps:</span>
          {courses.map((c, i) => (
            <span
              key={c.gap}
              className={`inline-flex items-center gap-1.5 rounded-full bg-[#ffe1e1] px-3 py-1 text-[#8a1c1c] transition-all duration-500 ${
                inView ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
              }`}
              style={{ transitionDelay: `${i * 120}ms` }}
            >
              <span aria-hidden="true" className="size-1.5 rounded-full bg-[#e5484d]" />
              {c.gap}
            </span>
          ))}
          <span className="rounded-full bg-[#f0ece5] px-2.5 py-1 text-[12px] text-[#5c5a55]">Example plan</span>
        </div>
      </div>

      <div className="relative mt-6">
        {/* Moving dashed path behind the three cards (desktop) */}
        <svg aria-hidden="true" className="absolute left-[8%] right-[8%] top-[46px] hidden h-2 w-[84%] lg:block" preserveAspectRatio="none" viewBox="0 0 100 2">
          <line x1="0" y1="1" x2="100" y2="1" stroke="#c9bdfd" strokeWidth="2" strokeDasharray="3 3" vectorEffect="non-scaling-stroke" className="dash-flow" />
        </svg>

        <ol className="relative grid gap-4 lg:grid-cols-3">
          {courses.map((c, i) => (
            <li
              key={c.gap}
              className={`transition-all duration-700 ease-[cubic-bezier(0.2,0.8,0.2,1)] motion-reduce:transition-none ${
                inView ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
              }`}
              style={{ transitionDelay: `${250 + i * 160}ms` }}
            >
              <SpotlightCard
                glow={c.tone.glow}
                className={`h-full rounded-[22px] p-5 ring-1 transition-transform duration-300 hover:-translate-y-1 motion-reduce:transition-none ${c.tone.card}`}
              >
                <div className="flex items-center gap-3">
                  <span className={`grid size-11 shrink-0 place-items-center rounded-2xl shadow-[0_10px_20px_-10px_rgba(0,0,0,0.4)] ${c.tone.icon}`}>
                    <c.icon className="size-5" aria-hidden="true" />
                  </span>
                  <span className="text-[12.5px] font-bold text-[#8a877f]">Step {i + 1}</span>
                  <span className={`ml-auto rounded-full px-2.5 py-0.5 text-[12px] font-bold ${c.tone.chip}`}>{c.status}</span>
                </div>
                <p className="mt-4 text-[12.5px] font-bold uppercase tracking-[0.08em] text-[#8a877f]">Closes: {c.gap}</p>
                <h4 className="mt-0.5 font-editorial text-[21px] font-semibold leading-tight">{c.title}</h4>
                <ul className="mt-3 space-y-1.5 text-[14px] text-[#4a4843]">
                  {c.topics.map((topic) => (
                    <li key={topic} className="flex items-start gap-2">
                      <Check className="mt-0.5 size-3.5 shrink-0 text-[#2f9e64]" strokeWidth={3} aria-hidden="true" />
                      {topic}
                    </li>
                  ))}
                </ul>
                <div className="mt-4 flex items-center justify-between text-[12.5px] font-semibold text-[#5c5a55]">
                  <span className="inline-flex items-center gap-1.5">
                    <Layers className="size-3.5" aria-hidden="true" /> {c.lessons} lessons
                  </span>
                  <span>Mastery {c.mastery}%</span>
                </div>
                <div className="mt-1.5 h-2 rounded-full bg-white ring-1 ring-black/5">
                  <div
                    className={`h-full rounded-full transition-[width] duration-[1200ms] ease-[cubic-bezier(0.2,0.8,0.2,1)] motion-reduce:transition-none ${c.tone.bar}`}
                    style={{ width: inView ? `${c.mastery}%` : "0%", transitionDelay: `${600 + i * 160}ms` }}
                  />
                </div>
              </SpotlightCard>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

/* ───────────────────────── live mock interview ───────────────────────── */

const QUESTION = "Tell me about a project where you worked in a team. What was your part?";
const FEEDBACK = [
  { label: "Technical accuracy", value: 80 },
  { label: "Clarity", value: 70 },
  { label: "Relevance", value: 90 },
];

type InterviewPhase = "ask" | "listen" | "feedback";

function InterviewDemo() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref);
  const reduced = useReducedMotion();
  const [phase, setPhase] = useState<InterviewPhase>("ask");
  const [typed, setTyped] = useState(0);

  useEffect(() => {
    if (!inView || reduced) return;
    let timer: ReturnType<typeof setTimeout>;
    if (phase === "ask") {
      timer = typed < QUESTION.length ? setTimeout(() => setTyped(typed + 1), 32) : setTimeout(() => setPhase("listen"), 700);
    } else if (phase === "listen") {
      timer = setTimeout(() => setPhase("feedback"), 2800);
    } else {
      timer = setTimeout(() => {
        setTyped(0);
        setPhase("ask");
      }, 6000);
    }
    return () => clearTimeout(timer);
  }, [inView, reduced, phase, typed]);

  const shownPhase: InterviewPhase = reduced ? "feedback" : phase;
  const text = reduced ? QUESTION : QUESTION.slice(0, typed);

  return (
    <div ref={ref} className="rounded-[20px] bg-[#1b1530] p-4 text-white shadow-[0_24px_50px_-30px_rgba(27,21,48,0.9)]">
      <div className="flex items-center gap-3">
        <span className="relative grid size-11 place-items-center rounded-full bg-linear-to-br from-[#8b6bff] to-[#eba0ff] text-[17px] font-bold">
          E
          {shownPhase === "ask" && <span aria-hidden="true" className="absolute inset-0 animate-ping rounded-full bg-[#8b6bff]/40 motion-reduce:hidden" />}
        </span>
        <span className="leading-tight">
          <span className="block font-semibold">Elena</span>
          <span className="text-[12.5px] text-white/60">AI interviewer · Software Engineer</span>
        </span>
        <span className="ml-auto inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-[12px] font-semibold">
          <span aria-hidden="true" className="size-1.5 animate-pulse rounded-full bg-[#ff6b6b]" /> Live
        </span>
      </div>

      <p className="mt-4 min-h-[72px] rounded-2xl rounded-tl-sm bg-white/10 px-4 py-3 text-[15px]">
        &ldquo;{text}
        {shownPhase === "ask" && <span aria-hidden="true" className="ml-0.5 inline-block h-4 w-0.5 translate-y-0.5 animate-pulse bg-white" />}
        {text.length === QUESTION.length && "”"}
      </p>

      {/* Listening: a moving sound wave, then the feedback */}
      <div className="mt-4 min-h-[76px]">
        {shownPhase === "listen" && (
          <div className="journey-in flex items-center gap-3 rounded-xl bg-white/[0.06] px-4 py-3">
            <Mic className="size-4 text-[#d0ffa4]" aria-hidden="true" />
            <span className="text-[13px] text-white/70">Listening to your answer…</span>
            <span aria-hidden="true" className="ml-auto flex h-8 items-end gap-[3px]">
              {Array.from({ length: 18 }, (_, i) => (
                <span key={i} className="wave-bar w-[3px] rounded-full bg-[#d0ffa4]" style={{ animationDelay: `${(i * 97) % 600}ms` }} />
              ))}
            </span>
          </div>
        )}
        {shownPhase === "feedback" && (
          <div className="journey-in">
            <div className="grid gap-2 sm:grid-cols-3">
              {FEEDBACK.map(({ label, value }, i) => (
                <FeedbackBar key={label} label={label} value={value} delay={i * 150} />
              ))}
            </div>
            <p className="mt-2.5 flex items-start gap-2 text-[13px] text-white/75">
              <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-[#ffd66b]" aria-hidden="true" />
              Tip: give one concrete example and say what the result was.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function FeedbackBar({ label, value, delay }: { label: string; value: number; delay: number }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const frame = requestAnimationFrame(() => setWidth(value));
    return () => cancelAnimationFrame(frame);
  }, [value]);
  return (
    <div className="rounded-xl bg-white/[0.06] px-3 py-2">
      <p className="flex justify-between text-[12px] text-white/60">
        {label}
        <span className="font-semibold text-white/80">{value}</span>
      </p>
      <div className="mt-1.5 h-1.5 rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-[#d0ffa4] transition-[width] duration-1000 ease-out motion-reduce:transition-none"
          style={{ width: `${width}%`, transitionDelay: `${delay}ms` }}
        />
      </div>
    </div>
  );
}

/* ───────────────────────── live Edu Assistant chat ───────────────────────── */

const ASK = "What's the difference between an INNER JOIN and a LEFT JOIN?";
const ANSWER =
  "An INNER JOIN keeps only the rows that match in both tables. A LEFT JOIN keeps every row from the left table and fills the missing matches with NULL.";
const WORDS = ANSWER.split(" ");

type ChatPhase = "idle" | "ask" | "typing" | "answer" | "sources";

function ChatDemo() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref);
  const reduced = useReducedMotion();
  const [phase, setPhase] = useState<ChatPhase>("idle");
  const [words, setWords] = useState(0);

  useEffect(() => {
    if (!inView || reduced) return;
    let timer: ReturnType<typeof setTimeout>;
    if (phase === "idle") timer = setTimeout(() => setPhase("ask"), 300);
    else if (phase === "ask") timer = setTimeout(() => setPhase("typing"), 900);
    else if (phase === "typing") timer = setTimeout(() => setPhase("answer"), 1400);
    else if (phase === "answer") {
      timer = words < WORDS.length ? setTimeout(() => setWords(words + 1), 55) : setTimeout(() => setPhase("sources"), 300);
    } else {
      timer = setTimeout(() => {
        setWords(0);
        setPhase("idle");
      }, 6500);
    }
    return () => clearTimeout(timer);
  }, [inView, reduced, phase, words]);

  const shown: ChatPhase = reduced ? "sources" : phase;
  const answer = reduced ? ANSWER : WORDS.slice(0, words).join(" ");

  return (
    <div ref={ref} className="min-h-[232px] space-y-3 rounded-[20px] bg-white p-4 shadow-[0_18px_40px_-28px_rgba(20,60,40,0.6)]">
      {shown !== "idle" && (
        <p className="journey-in ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-sm bg-[#145a36] px-4 py-2.5 text-[14.5px] text-white">{ASK}</p>
      )}
      {shown === "typing" && (
        <div aria-hidden="true" className="journey-in flex w-fit gap-1 rounded-2xl rounded-bl-sm bg-[#f3f1ec] px-4 py-3.5">
          {[0, 1, 2].map((i) => (
            <span key={i} className="edu-dot size-2 rounded-full bg-[#5c5a55]" style={{ animationDelay: `${i * 160}ms` }} />
          ))}
        </div>
      )}
      {(shown === "answer" || shown === "sources") && (
        <div className="max-w-[92%] rounded-2xl rounded-bl-sm bg-[#f3f1ec] px-4 py-3 text-[14.5px]">
          {answer}
          {shown === "answer" && <span aria-hidden="true" className="ml-0.5 inline-block h-4 w-0.5 translate-y-0.5 animate-pulse bg-[#145a36]" />}
          {shown === "sources" && (
            <span className="mt-2 flex flex-wrap gap-1.5 text-[12px] font-semibold">
              {["Source 1", "Source 2"].map((label, i) => (
                <span
                  key={label}
                  className="journey-in inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 text-[#145a36] ring-1 ring-[#cfe9da]"
                  style={{ animationDelay: `${i * 140}ms` }}
                >
                  <BookOpen className="size-3" aria-hidden="true" /> {label}
                </span>
              ))}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

/* ───────────────────────── section ───────────────────────── */

/** Learn and practise: a learning path built from the skill gaps, then a live mock interview demo and a
 *  live Edu Assistant chat demo. Soft colour blobs drift in the background. */
export function PracticePreview() {
  return (
    <section aria-labelledby="practice-heading" className="relative isolate overflow-clip bg-white py-16 lg:py-24">
      {/* Drifting colour blobs */}
      <div aria-hidden="true" className="blob-drift absolute -left-32 top-10 -z-10 size-[420px] rounded-full bg-[#e9e2ff] blur-3xl" />
      <div aria-hidden="true" className="blob-drift absolute -right-24 top-1/3 -z-10 size-[380px] rounded-full bg-[#d5f5e3] blur-3xl [animation-delay:-6s]" />
      <div aria-hidden="true" className="blob-drift absolute bottom-0 left-1/3 -z-10 size-[340px] rounded-full bg-[#ffe3f1] blur-3xl [animation-delay:-11s]" />

      <div className="mx-auto max-w-[1240px] px-4 sm:px-8">
        <Reveal className="text-center">
          <p className="text-[13px] font-extrabold uppercase tracking-[0.12em] text-[#5b3df5]">Learn and practise</p>
          <h2 id="practice-heading" className="mx-auto mt-3 max-w-[680px] font-editorial text-[clamp(32px,3.6vw,46px)] font-semibold leading-[1.08] tracking-[-0.01em]">
            Practise like it&rsquo;s <em className="text-[#5b3df5]">the real thing.</em>
          </h2>
          <p className="mx-auto mt-3 max-w-[560px] text-[16.5px] text-[#5c5a55]">
            Your skill gaps become a personal learning path. Then you practise until you&rsquo;re ready.
          </p>
        </Reveal>

        <Reveal delay={100} className="mt-10">
          <LearningPath />
        </Reveal>

        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <Reveal delay={100} className="h-full">
            <SpotlightCard glow="rgba(109,74,255,0.18)" className="h-full rounded-[26px] bg-[#efe8ff] p-5 sm:p-7">
              <article aria-labelledby="mock-interview-heading" className="flex h-full flex-col">
                <InterviewDemo />
                <div className="mt-5 flex flex-1 flex-col">
                  <p className="inline-flex items-center gap-2 text-[13px] font-extrabold uppercase tracking-[0.08em] text-[#4a2fd0]">
                    <Video className="size-4" aria-hidden="true" /> Mock interview
                  </p>
                  <h3 id="mock-interview-heading" className="mt-1.5 font-editorial text-[26px] font-semibold leading-tight">
                    Answer real questions, get instant feedback.
                  </h3>
                  <p className="mt-2 text-[15.5px] text-[#4a4843]">
                    A video interviewer asks questions for your role, listens to your answer and tells you how to improve.
                    Recordings are optional and go straight to your own Google Drive.
                  </p>
                  <Link href="/mock-interview" className="mt-auto inline-flex min-h-11 items-center gap-1.5 self-start pt-4 font-extrabold text-[#4a2fd0] hover:underline">
                    Try a mock interview <ArrowRightIcon className="size-4" strokeWidth={2.4} />
                  </Link>
                </div>
              </article>
            </SpotlightCard>
          </Reveal>

          <Reveal delay={240} className="h-full">
            <SpotlightCard glow="rgba(47,158,100,0.18)" className="h-full rounded-[26px] bg-[#d5f5e3] p-5 sm:p-7">
              <article aria-labelledby="edu-assistant-heading" className="flex h-full flex-col">
                <ChatDemo />
                <div className="mt-5 flex flex-1 flex-col">
                  <p className="inline-flex items-center gap-2 text-[13px] font-extrabold uppercase tracking-[0.08em] text-[#145a36]">
                    <BookOpen className="size-4" aria-hidden="true" /> Edu Assistant
                  </p>
                  <h3 id="edu-assistant-heading" className="mt-1.5 font-editorial text-[26px] font-semibold leading-tight">
                    Ask anything while you learn.
                  </h3>
                  <p className="mt-2 text-[15.5px] text-[#3d4a42]">
                    Stuck on a topic from your learning path? The Edu Assistant explains it simply and shows where each
                    answer comes from.
                  </p>
                  <Link href="/edu-assistant" className="mt-auto inline-flex min-h-11 items-center gap-1.5 self-start pt-4 font-extrabold text-[#145a36] hover:underline">
                    Ask the Edu Assistant <ArrowRightIcon className="size-4" strokeWidth={2.4} />
                  </Link>
                </div>
              </article>
            </SpotlightCard>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

