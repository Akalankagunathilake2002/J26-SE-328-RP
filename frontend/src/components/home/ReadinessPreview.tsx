import { Check, Link2 } from "lucide-react";
import Link from "next/link";

import { ArrowRightIcon } from "@/components/icons";

import { Reveal } from "./Reveal";

const points = [
  "A readiness score weighted by how often employers ask for each skill.",
  "Related skills count too: AWS can count towards Cloud Computing, but only through a verified link.",
  "Your gaps ranked, so you know what to learn first.",
];

/** Skill analysis: the text on one side and an example readiness report (clearly labelled as an example). */
export function ReadinessPreview() {
  return (
    <section aria-labelledby="readiness-heading" className="mx-auto max-w-[1240px] px-4 py-16 sm:px-8 lg:py-20">
      <div className="grid items-center gap-10 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] lg:gap-14">
        <Reveal>
          <p className="text-[13px] font-extrabold uppercase tracking-[0.12em] text-[#5b3df5]">Skill analysis</p>
          <h2 id="readiness-heading" className="mt-3 font-editorial text-[clamp(32px,3.6vw,46px)] font-semibold leading-[1.08] tracking-[-0.01em]">
            Know exactly <em className="text-[#5b3df5]">where you stand.</em>
          </h2>
          <p className="mt-3 max-w-[500px] text-[16.5px] text-[#5c5a55]">
            Pick a job role and Skillaro compares your evidence-backed skills with what employers ask for in real job ads.
          </p>
          <ul className="mt-6 space-y-3">
            {points.map((point) => (
              <li key={point} className="flex gap-3 text-[15.5px]">
                <span aria-hidden="true" className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-[#efe8ff] text-[#5b3df5]">
                  <Check className="size-3.5" strokeWidth={3} />
                </span>
                {point}
              </li>
            ))}
          </ul>
          <Link
            href="/skill-analysis"
            className="mt-7 inline-flex min-h-12 items-center gap-2 rounded-full bg-[#5b3df5] px-6 text-[16px] font-bold text-white shadow-[0_14px_30px_-14px_rgba(91,61,245,0.9)] transition hover:-translate-y-0.5 hover:bg-[#4a2fd0] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30"
          >
            See your skill analysis
            <ArrowRightIcon className="size-[18px]" strokeWidth={2.4} />
          </Link>
        </Reveal>

        <Reveal delay={150}>
          <ExampleReport />
        </Reveal>
      </div>
    </section>
  );
}

function ExampleReport() {
  return (
    <figure className="rounded-[26px] border border-[#e6e2da] bg-white p-5 shadow-[0_30px_60px_-36px_rgba(40,30,10,0.6)] sm:p-7">
      <figcaption className="flex flex-wrap items-center justify-between gap-2">
        <span>
          <span className="block text-[12.5px] font-bold uppercase tracking-[0.08em] text-[#8a877f]">Readiness report</span>
          <span className="font-editorial text-[22px] font-semibold">Software Engineer</span>
        </span>
        <span className="rounded-full bg-[#f0ece5] px-3 py-1 text-[12.5px] font-bold text-[#5c5a55]">Example</span>
      </figcaption>

      <div className="mt-5 grid gap-5 sm:grid-cols-[150px_1fr] sm:items-center">
        {/* Score ring */}
        <div
          className="mx-auto grid size-[140px] place-items-center rounded-full"
          style={{ background: "conic-gradient(#5b3df5 0 72%, #ece8ff 72% 100%)" }}
        >
          <div className="grid size-[112px] place-items-center rounded-full bg-white text-center">
            <span>
              <span className="block font-editorial text-[38px] font-semibold leading-none">72%</span>
              <span className="text-[12.5px] font-bold text-[#5b3df5]">ready</span>
            </span>
          </div>
        </div>

        <div className="space-y-3 text-[13.5px] font-semibold">
          <ChipRow label="You have" tone="bg-[#d5f5e3] text-[#145a36]" chips={["Python", "SQL", "Git", "HTML & CSS"]} />
          <div>
            <p className="mb-1.5 text-[12.5px] font-bold text-[#8a877f]">Counts through a related skill</p>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[#dbeeff] px-3 py-1 text-[#0b4a80]">
              AWS <Link2 aria-label="counts towards" className="size-3.5" /> Cloud Computing
            </span>
          </div>
          <ChipRow label="Gaps to close" tone="bg-[#ffe1e1] text-[#8a1c1c]" chips={["REST APIs", "CI/CD", "Testing"]} />
        </div>
      </div>

      <div className="mt-6 rounded-2xl bg-[#f7f5f1] p-4">
        <p className="text-[12.5px] font-bold uppercase tracking-[0.08em] text-[#8a877f]">Learn next</p>
        <ol className="mt-2 grid gap-2 sm:grid-cols-3">
          {["REST APIs", "CI/CD", "Testing"].map((skill, i) => (
            <li key={skill} className="flex items-center gap-2.5 rounded-xl bg-white px-3 py-2.5 text-[14px] font-semibold ring-1 ring-[#ebe7df]">
              <span className="grid size-6 shrink-0 place-items-center rounded-full bg-[#5b3df5] text-[12px] font-bold text-white">{i + 1}</span>
              {skill}
            </li>
          ))}
        </ol>
      </div>
    </figure>
  );
}

function ChipRow({ label, tone, chips }: { label: string; tone: string; chips: string[] }) {
  return (
    <div>
      <p className="mb-1.5 text-[12.5px] font-bold text-[#8a877f]">{label}</p>
      <ul className="flex flex-wrap gap-1.5">
        {chips.map((chip) => (
          <li key={chip} className={`rounded-full px-3 py-1 ${tone}`}>
            {chip}
          </li>
        ))}
      </ul>
    </div>
  );
}
