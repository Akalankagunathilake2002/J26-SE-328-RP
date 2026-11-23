"use client";

import { useEffect, useRef, useState } from "react";

import { StarIcon } from "@/components/icons";

const steps = [
  { label: "Your Evidence", dot: "bg-pink", text: "Add your CV, projects, certificates and GitHub." },
  { label: "Your Skills", dot: "bg-brand-blue", text: "We turn your evidence into a skill profile." },
  { label: "Industry Demand", dot: "bg-lime", star: true, text: "We compare it with what real job ads ask for." },
  { label: "Your Career Path", dot: "bg-[#9fe35f]", text: "You get your gaps and a clear path to close them." },
];

const STEP_MS = 1500; // time per step
const HOLD_MS = 2600; // pause on the last step before it plays again

/** Evidence → career path journey in the hero card, played step by step: the line grows with a spark at
 *  its tip, each dot lights up and pulses as the line reaches it, and a caption explains the step. It
 *  plays while the card is on screen, holds on the last step and starts again. With reduced motion every
 *  step is shown complete. */
export function JourneySteps() {
  const ref = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(steps.length - 1); // complete until the animation starts
  const [playing, setPlaying] = useState(false);

  // Play only while the card is visible (and never with reduced motion).
  useEffect(() => {
    const el = ref.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const observer = new IntersectionObserver(([entry]) => {
      setPlaying(entry.isIntersecting);
      if (entry.isIntersecting) setActive(0);
    }, { threshold: 0.4 });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!playing) return;
    const last = active === steps.length - 1;
    const timer = setTimeout(() => setActive(last ? 0 : active + 1), last ? HOLD_MS : STEP_MS);
    return () => clearTimeout(timer);
  }, [active, playing]);

  // Dot centres sit at 12.5% and 87.5% of the row (four equal columns).
  const progress = active / (steps.length - 1);
  const head = `${12.5 + progress * 75}%`;
  const moving = "transition-all duration-[1100ms] ease-[cubic-bezier(0.45,0,0.2,1)] motion-reduce:transition-none";

  return (
    <div ref={ref}>
      <ol aria-label="How Skillaro works, step by step" className="relative grid grid-cols-4 gap-1">
        {/* Grey track, coloured fill and the spark at its tip, behind the dots */}
        <span aria-hidden="true" className="absolute bottom-[10px] left-[12.5%] right-[12.5%] h-0.5 bg-[#ebe7df]" />
        <span
          aria-hidden="true"
          className={`absolute bottom-[9.5px] left-[12.5%] h-[3px] rounded-full bg-linear-to-r from-pink via-brand-blue to-[#9fe35f] ${moving}`}
          style={{ width: `${progress * 75}%` }}
        />
        <span
          aria-hidden="true"
          className={`absolute bottom-[5px] size-3 -translate-x-1/2 rounded-full bg-white shadow-[0_0_0_3px_rgba(109,74,255,0.35),0_0_14px_4px_rgba(109,74,255,0.45)] ${moving} ${
            active === 0 ? "opacity-0" : "opacity-100"
          }`}
          style={{ left: head }}
        />

        {steps.map((step, i) => {
          const reached = i <= active;
          const current = i === active;
          return (
            <li key={step.label} aria-current={current ? "step" : undefined} className="flex flex-col items-center gap-2.5 text-center">
              <span
                className={`flex h-9 items-end text-[12.5px] font-bold leading-tight transition-colors duration-500 sm:h-auto ${
                  reached ? "text-[#141413]" : "text-[#a29f97]"
                }`}
              >
                {step.label}
              </span>
              <span className="relative grid h-[22px] w-full place-items-center">
                {/* Pulse ring when the line reaches this dot */}
                {current && (
                  <span
                    key={`ring-${active}`}
                    aria-hidden="true"
                    className={`journey-ring absolute size-[22px] rounded-full ${step.dot}`}
                  />
                )}
                <span
                  aria-hidden="true"
                  className={`relative grid place-items-center rounded-full ring-4 ring-white transition-[transform,background-color] duration-500 motion-reduce:transition-none ${
                    step.star ? "size-[22px]" : "size-4"
                  } ${reached ? `${step.dot} scale-100` : "scale-75 bg-[#e3dfd7]"} ${current ? "scale-125" : ""}`}
                >
                  {step.star && <StarIcon className={`size-3 ${reached ? "text-[#141413]" : "text-white"}`} strokeWidth={2.6} />}
                </span>
              </span>
            </li>
          );
        })}
      </ol>

      {/* What the current step means */}
      <p className="mt-3 flex min-h-[22px] items-center justify-center gap-2 text-center text-[13.5px] text-[#5c5a55]">
        <span key={active} className="journey-in">
          <span className="font-bold text-[#141413]">
            {active + 1}. {steps[active].label}:
          </span>{" "}
          {steps[active].text}
        </span>
      </p>
    </div>
  );
}
