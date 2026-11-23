"use client";

import { Check, Plus } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useId, useRef, useState, type CSSProperties } from "react";

import { ArrowRightIcon } from "@/components/icons";

import { Reveal } from "./Reveal";

const SIZE = 172;
const STROKE = 12;
const RADIUS = (SIZE - STROKE) / 2 - 8;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const COLORS = ["#6d4aff", "#d0ffa4", "#eba0ff", "#ffd66b", "#4cc38a", "#006ee9"];
const CONFETTI = Array.from({ length: 26 }, (_, i) => {
  const angle = (i / 26) * Math.PI * 2;
  const distance = 100 + ((i * 37) % 60);
  return {
    dx: Math.round(Math.cos(angle) * distance),
    dy: Math.round(Math.sin(angle) * distance),
    rot: `${(i * 53) % 360}deg`,
    color: COLORS[i % COLORS.length],
    delay: `${(i % 5) * 40}ms`,
    wide: i % 2 === 0,
  };
});

/** Background slideshow: free Pexels photos of students (Tima Miroshnichenko, Mikhail Nilov, Yan Krukau). */
const SLIDES = ["/illustrations/faq-1.jpg", "/illustrations/faq-2.jpg", "/illustrations/faq-3.jpg", "/illustrations/faq-4.jpg"];
const SLIDE_MS = 5000;

/** FAQ as a small game: every question opened for the first time fills the readiness ring a step. While
 *  it isn't full, a dashed ring spins slowly around it. When every question has been read, the ring turns
 *  green, confetti bursts and it says "You're ready for your career!". Answers slide open smoothly and
 *  one question is open at a time. */
export function FaqSection({ items }: { items: { q: string; a: string }[] }) {
  const [open, setOpen] = useState<number | null>(null);
  const [read, setRead] = useState<ReadonlySet<number>>(() => new Set());
  const baseId = useId();
  const sectionRef = useRef<HTMLElement>(null);
  const [slide, setSlide] = useState(0);

  // Change the background photo every few seconds, only while the FAQ is on screen (and never with reduced motion).
  useEffect(() => {
    const el = sectionRef.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let timer: ReturnType<typeof setInterval> | undefined;
    const observer = new IntersectionObserver(([entry]) => {
      clearInterval(timer);
      if (entry.isIntersecting) timer = setInterval(() => setSlide((n) => (n + 1) % SLIDES.length), SLIDE_MS);
    });
    observer.observe(el);
    return () => {
      observer.disconnect();
      clearInterval(timer);
    };
  }, []);

  const total = items.length;
  const done = read.size;
  const complete = done === total;

  const toggle = (i: number) => {
    setOpen(open === i ? null : i);
    if (!read.has(i)) setRead(new Set(read).add(i));
  };

  return (
    <section ref={sectionRef} id="faq" aria-labelledby="faq-heading" className="relative isolate scroll-mt-28 overflow-clip py-16 lg:py-24">
      {/* Background: photos of students that crossfade every few seconds, each slowly zooming, under a light
          purple-white wash so the text and cards stay easy to read. */}
      {SLIDES.map((src, i) => (
        <Image
          key={src}
          src={src}
          alt=""
          fill
          sizes="100vw"
          loading={i === 0 ? "eager" : "lazy"}
          className={`faq-slide -z-20 object-cover object-[50%_35%] blur-[2px] transition-opacity duration-[1500ms] ease-in-out motion-reduce:transition-none ${
            i === slide ? "opacity-100" : "opacity-0"
          }`}
        />
      ))}
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10 bg-[linear-gradient(100deg,rgba(255,255,255,0.92)_0%,rgba(255,255,255,0.74)_45%,rgba(239,232,255,0.58)_100%)]"
      />
      <div aria-hidden="true" className="absolute inset-x-0 top-0 -z-10 h-24 bg-linear-to-b from-[#f4f2ee] to-transparent" />
      <div aria-hidden="true" className="absolute inset-x-0 bottom-0 -z-10 h-24 bg-linear-to-t from-[#f4f2ee] to-transparent" />
      <div className="mx-auto grid max-w-[1240px] gap-8 px-4 sm:px-8 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:gap-14">
        <div className="lg:sticky lg:top-28 lg:self-start">
          <Reveal>
            <p className="text-[13px] font-extrabold uppercase tracking-[0.12em] text-[#5b3df5]">FAQ</p>
            <h2 id="faq-heading" className="mt-3 font-editorial text-[clamp(32px,3.6vw,46px)] font-semibold leading-[1.08] tracking-[-0.01em]">
              Questions, <em className="text-[#5b3df5]">answered.</em>
            </h2>
            <p className="mt-3 max-w-[400px] text-[16px] text-[#5c5a55]">
              Can&rsquo;t find what you need? Ask the{" "}
              <Link href="/edu-assistant" className="font-bold text-[#5b3df5] underline-offset-4 hover:underline">
                Edu Assistant
              </Link>
              .
            </p>
          </Reveal>

          <Reveal delay={120}>
            <div
              className={`mt-6 flex flex-col items-center gap-5 rounded-[26px] border p-6 text-center shadow-[0_24px_50px_-32px_rgba(74,47,208,0.55)] backdrop-blur-md transition-colors duration-700 sm:flex-row sm:text-left ${
                complete ? "border-[#bfe8cf] bg-linear-to-br from-[#e9f9ef]/95 to-white/90" : "border-[#e4dcff] bg-linear-to-br from-[#f4f0ff]/95 to-white/90"
              }`}
            >
              <ReadinessRing done={done} total={total} complete={complete} />

              <div aria-live="polite" className="min-w-0">
                {complete ? (
                  <div key="complete" className="journey-in">
                    <p className="font-editorial text-[24px] font-semibold leading-tight text-[#1d7a47]">
                      You&rsquo;re ready for your career!
                    </p>
                    <p className="mt-1.5 text-[14.5px] text-[#4a4843]">You know how Skillaro works. Time to start your journey.</p>
                    <Link
                      href="/register"
                      className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-full bg-[#2f9e64] px-5 text-[15px] font-bold text-white shadow-[0_12px_26px_-12px_rgba(47,158,100,0.9)] transition hover:-translate-y-0.5 hover:bg-[#278a56] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#2f9e64]/30"
                    >
                      Create your account <ArrowRightIcon className="size-4" strokeWidth={2.4} />
                    </Link>
                  </div>
                ) : (
                  <div>
                    <p className="font-editorial text-[22px] font-semibold leading-tight">How career ready are you?</p>
                    <p className="mt-1.5 text-[14.5px] text-[#5c5a55]">
                      {done === 0 ? "Open each question to fill the ring." : `${total - done} more to go. Keep reading!`}
                    </p>
                    <ol aria-hidden="true" className="mt-3 flex justify-center gap-1.5 sm:justify-start">
                      {items.map(({ q }, i) => (
                        <li
                          key={q}
                          className={`h-2 w-6 rounded-full transition-colors duration-500 ${read.has(i) ? "bg-[#6d4aff]" : "bg-[#e6e0fa]"}`}
                        />
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            </div>
          </Reveal>
        </div>

        <div className="space-y-2.5">
          {items.map(({ q, a }, i) => {
            const isOpen = open === i;
            const isRead = read.has(i);
            const panelId = `${baseId}-panel-${i}`;
            const buttonId = `${baseId}-button-${i}`;
            return (
              <Reveal key={q} delay={i * 70}>
                <div
                  className={`rounded-2xl border transition-[background-color,box-shadow,border-color] duration-300 motion-reduce:transition-none ${
                    isOpen
                      ? "border-[#d9d0ff] bg-white shadow-[0_22px_44px_-30px_rgba(74,47,208,0.55)]"
                      : "border-white/70 bg-white/80 shadow-[0_10px_24px_-20px_rgba(40,30,10,0.45)] backdrop-blur-md hover:border-[#d9d0ff] hover:bg-white"
                  }`}
                >
                  <h3>
                    <button
                      type="button"
                      id={buttonId}
                      aria-expanded={isOpen}
                      aria-controls={panelId}
                      onClick={() => toggle(i)}
                      className="flex min-h-14 w-full items-center gap-3.5 rounded-2xl px-4 py-3 text-left text-[16.5px] font-bold focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/25 sm:px-5"
                    >
                      {/* Number, or a green tick once read */}
                      <span
                        className={`grid size-8 shrink-0 place-items-center rounded-xl text-[12.5px] font-extrabold transition-colors duration-500 ${
                          isRead ? "bg-[#d5f5e3] text-[#1d7a47]" : "bg-[#f0ece5] text-[#8a877f]"
                        }`}
                      >
                        {isRead ? (
                          <Check className="journey-in size-4" strokeWidth={3} aria-label="Read" />
                        ) : (
                          String(i + 1).padStart(2, "0")
                        )}
                      </span>
                      <span className="min-w-0 flex-1">{q}</span>
                      <span
                        aria-hidden="true"
                        className={`grid size-8 shrink-0 place-items-center rounded-full transition-[transform,background-color,color] duration-300 motion-reduce:transition-none ${
                          isOpen ? "rotate-45 bg-[#5b3df5] text-white" : "bg-[#efe8ff] text-[#5b3df5]"
                        }`}
                      >
                        <Plus className="size-4" strokeWidth={2.6} />
                      </span>
                    </button>
                  </h3>
                  <div
                    id={panelId}
                    role="region"
                    aria-labelledby={buttonId}
                    className={`grid transition-[grid-template-rows] duration-400 ease-[cubic-bezier(0.2,0.8,0.2,1)] motion-reduce:transition-none ${
                      isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                    }`}
                  >
                    <div className="overflow-hidden" inert={!isOpen}>
                      <p
                        className={`pb-5 pl-[62px] pr-5 text-[15px] leading-relaxed text-[#5c5a55] transition-[opacity,transform] duration-400 motion-reduce:transition-none sm:pl-[66px] ${
                          isOpen ? "translate-y-0 opacity-100 delay-100" : "-translate-y-2 opacity-0"
                        }`}
                      >
                        {a}
                      </p>
                    </div>
                  </div>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function ReadinessRing({ done, total, complete }: { done: number; total: number; complete: boolean }) {
  const offset = CIRCUMFERENCE * (1 - done / total);
  return (
    <div className="relative grid size-[172px] shrink-0 place-items-center">
      {/* Spinner: a dashed ring turning slowly until every question has been read */}
      <span
        aria-hidden="true"
        className={`absolute inset-0 rounded-full border-2 border-dashed transition-opacity duration-700 motion-safe:animate-[spin_14s_linear_infinite] ${
          complete ? "border-[#2f9e64]/40 opacity-0" : "border-[#b8a6ff] opacity-100"
        }`}
      />

      <svg aria-hidden="true" viewBox={`0 0 ${SIZE} ${SIZE}`} className="absolute inset-0 -rotate-90">
        <defs>
          <linearGradient id="faq-ring" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#6d4aff" />
            <stop offset="100%" stopColor="#eba0ff" />
          </linearGradient>
        </defs>
        <circle cx={SIZE / 2} cy={SIZE / 2} r={RADIUS} fill="white" stroke="#ece8ff" strokeWidth={STROKE} />
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke={complete ? "#2f9e64" : "url(#faq-ring)"}
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-[900ms] ease-[cubic-bezier(0.2,0.8,0.2,1)] motion-reduce:transition-none"
        />
      </svg>

      <div role="img" aria-label={`${done} of ${total} questions read`} className="relative text-center">
        {complete ? (
          <span key="done" className="journey-in grid place-items-center">
            <span className="grid size-12 place-items-center rounded-full bg-[#2f9e64] text-white">
              <Check className="size-6" strokeWidth={3} aria-hidden="true" />
            </span>
            <span className="mt-1.5 text-[14px] font-extrabold text-[#1d7a47]">Ready!</span>
          </span>
        ) : (
          <span key={done} className="journey-in block">
            <span className="block font-editorial text-[36px] font-semibold leading-none">
              {done}
              <span className="text-[22px] text-[#a29f97]">/{total}</span>
            </span>
            <span className="text-[12.5px] font-bold uppercase tracking-[0.08em] text-[#6d4aff]">read</span>
          </span>
        )}
      </div>

      {/* Confetti when the ring is full */}
      {complete && (
        <div aria-hidden="true" className="pointer-events-none absolute inset-0">
          {CONFETTI.map((piece, i) => (
            <span
              key={i}
              className={`faq-confetti absolute left-1/2 top-1/2 rounded-[2px] ${piece.wide ? "h-1.5 w-3.5" : "h-3.5 w-2"}`}
              style={
                {
                  background: piece.color,
                  animationDelay: piece.delay,
                  "--dx": `${piece.dx}px`,
                  "--dy": `${piece.dy}px`,
                  "--rot": piece.rot,
                } as CSSProperties
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
