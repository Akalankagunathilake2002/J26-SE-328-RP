"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Bot, Sparkles, X, GraduationCap, ListChecks, MessageCircle } from "lucide-react";

// What the assistant says in its bubble, in turn (types each one out)
const MESSAGES = [
  "Hi, I'm Skillaro, your learning assistant!",
  "Let's learn new things today.",
  "Pick a topic and I'll teach it step by step.",
  "Want a quick quiz? It takes two minutes.",
];

// Quick starts shown on hover
const QUICK_STARTS = [
  { icon: GraduationCap, text: "Let's learn something new" },
  { icon: MessageCircle, text: "Ask me anything about your field" },
  { icon: ListChecks, text: "Quiz me on a topic" },
];

const FIRST_DELAY_MS = 1200;
const TYPING_MS = 900;
const MESSAGE_MS = 4800;

/** Floating Edu Assistant button for the home page: a live bubble that cycles friendly messages, and quick
 *  starts on hover. Everything links to /edu-assistant (which asks for a login first if needed). */
export function EduAssistantFab() {
  const [index, setIndex] = useState(0);
  const [typing, setTyping] = useState(true);
  const [started, setStarted] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [hovered, setHovered] = useState(false);

  useEffect(() => {
    let typingTimer: ReturnType<typeof setTimeout>;
    const showNext = (next: number) => {
      setIndex(next);
      setTyping(true);
      typingTimer = setTimeout(() => setTyping(false), TYPING_MS);
    };
    const first = setTimeout(() => {
      setStarted(true);
      showNext(0);
    }, FIRST_DELAY_MS);
    let n = 0;
    const cycle = setInterval(() => showNext(++n % MESSAGES.length), MESSAGE_MS);
    return () => {
      clearTimeout(first);
      clearTimeout(typingTimer);
      clearInterval(cycle);
    };
  }, []);

  const showBubble = hovered || (started && !dismissed);

  return (
    <div
      className="fixed z-40 flex flex-col items-end gap-3"
      style={{
        right: "max(20px, calc(env(safe-area-inset-right, 0px) + 16px))",
        bottom: "max(20px, calc(env(safe-area-inset-bottom, 0px) + 16px))",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setHovered(true)}
      onBlur={() => setHovered(false)}
    >
      {hovered && (
        <ul className="edu-pop flex max-w-[260px] flex-col gap-2" aria-label="Quick starts">
          {QUICK_STARTS.map(({ icon: Icon, text }) => (
            <li key={text}>
              <Link
                href="/edu-assistant"
                className="flex items-center gap-2 border-2 border-ink bg-white px-3 py-2 text-sm font-semibold text-ink shadow-[3px_3px_0_var(--color-ink)] transition-transform hover:-translate-y-0.5 hover:bg-butter focus-visible:bg-butter focus-visible:outline-none"
              >
                <Icon className="size-4 shrink-0" aria-hidden="true" /> {text}
              </Link>
            </li>
          ))}
        </ul>
      )}

      {showBubble && (
        <div
          key={hovered ? "hover" : index}
          className="edu-pop relative max-w-[250px] border-2 border-ink bg-white px-4 py-3 pr-8 text-sm font-semibold text-ink shadow-[3px_3px_0_var(--color-ink)]"
          role="status"
          aria-live="polite"
        >
          {typing && !hovered ? (
            <span className="flex items-center gap-1 py-1" aria-label="Skillaro is typing">
              {[0, 1, 2].map((i) => (
                <span key={i} className="edu-dot size-1.5 rounded-full bg-ink" style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </span>
          ) : (
            <span>{hovered ? "Hi! What shall we learn today?" : MESSAGES[index]}</span>
          )}
          {!hovered && (
            <button
              type="button"
              onClick={() => setDismissed(true)}
              aria-label="Hide message"
              className="absolute right-1.5 top-1.5 grid size-6 place-items-center text-muted hover:text-ink focus-visible:text-ink focus-visible:outline-none"
            >
              <X className="size-3.5" />
            </button>
          )}
          {/* Bubble tail pointing at the button */}
          <span
            aria-hidden="true"
            className="absolute -bottom-[9px] right-6 size-4 rotate-45 border-b-2 border-r-2 border-ink bg-white"
          />
        </div>
      )}

      <Link
        href="/edu-assistant"
        aria-label="Open the Skillaro Edu Assistant"
        className="edu-bob relative grid size-16 place-items-center rounded-full border-2 border-ink bg-sun shadow-[4px_4px_0_var(--color-ink)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-brand-blue/40"
      >
        <span aria-hidden="true" className="edu-ring absolute inset-0 rounded-full border-2 border-pink" />
        <Bot className="size-8 text-ink" aria-hidden="true" />
        <span
          aria-hidden="true"
          className="edu-wave absolute -right-1 -top-1 grid size-6 place-items-center rounded-full border-2 border-ink bg-pink"
        >
          <Sparkles className="size-3.5 text-ink" />
        </span>
      </Link>
    </div>
  );
}
