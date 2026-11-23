import Image from "next/image";
import Link from "next/link";

import { ArrowRightIcon } from "@/components/icons";

import { HeroVideo } from "./HeroVideo";
import { JourneySteps } from "./JourneySteps";

const benefits = [
  { label: "Know what's in demand", tone: "bg-[#efe8ff] text-[#3b2394]" },
  { label: "Understand your strengths", tone: "bg-[#fff0bf] text-[#5c4200]" },
  { label: "Identify skill gaps", tone: "bg-[#ffdcee] text-[#7a1048]" },
  { label: "Learn what matters", tone: "bg-[#d5f5e3] text-[#145a36]" },
  { label: "Practice & get feedback", tone: "bg-[#dbeeff] text-[#0b4a80]" },
];

/** Video hero: the background video runs up under the floating header (the negative top margin equals
 *  the header's height: two rows on small screens, one row from lg). The journey card overlaps its bottom edge. */
export function Hero() {
  return (
    <>
      <section className="relative isolate -mt-[115px] flex min-h-[640px] items-center overflow-hidden bg-[#0d0b1a] text-white sm:min-h-[680px] lg:-mt-[75px] lg:min-h-[min(780px,94vh)]">
        <HeroVideo />
        {/* Darkens the video so the text stays readable: most at the top (under the header) and at the bottom. */}
        <div
          aria-hidden="true"
          className="absolute inset-0 -z-10 bg-[linear-gradient(to_bottom,rgba(13,11,26,0.78)_0%,rgba(13,11,26,0.5)_38%,rgba(13,11,26,0.55)_70%,rgba(13,11,26,0.9)_100%)]"
        />

        <div className="mx-auto w-full max-w-[1100px] px-4 pb-32 pt-[150px] text-center sm:px-8 lg:pt-[120px]">
          <p className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/10 px-3.5 py-1.5 text-[13.5px] font-bold backdrop-blur-sm">
            <span aria-hidden="true" className="size-2 rounded-full bg-lime" />
            AI-Powered Career Readiness Platform
          </p>

          <h1 className="mx-auto mt-[18px] max-w-[900px] font-editorial text-[clamp(40px,5.6vw,74px)] font-semibold leading-[1.04] tracking-[-0.02em] [text-shadow:0_2px_24px_rgba(0,0,0,0.35)]">
            Bridge what you know with <em className="text-lime">what industry needs.</em>
          </h1>

          <p className="mx-auto mt-4 max-w-[580px] text-[19px] text-white/85">
            Understand your skills, discover the gaps, and get a personalized path to become career ready.
          </p>

          <Link
            href="#how-it-works"
            className="mt-7 inline-flex min-h-[52px] items-center gap-2.5 rounded-full bg-[#6d4aff] px-7 text-[17px] font-bold text-white shadow-[0_14px_30px_-12px_rgba(109,74,255,0.9)] transition hover:-translate-y-0.5 hover:bg-[#5f3cf5] active:translate-y-0 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-white/40"
          >
            Explore How It Works
            <ArrowRightIcon className="size-[18px]" strokeWidth={2.4} />
          </Link>
        </div>
      </section>

      <div className="relative z-10 mx-auto -mt-20 max-w-[1100px] px-4 sm:px-8">
        <div className="grid items-center gap-6 rounded-[24px] border border-[#e6e2da] bg-white p-5 shadow-[0_28px_60px_-34px_rgba(40,30,10,0.55)] sm:p-7 md:grid-cols-[minmax(0,320px)_1fr] md:gap-8">
          <Image
            src="/photos/students-group.png"
            alt="Four students laughing together on their way to class"
            width={900}
            height={648}
            sizes="320px"
            className="mx-auto h-auto w-full max-w-[320px] drop-shadow-[0_14px_18px_rgba(40,30,10,0.18)]"
          />

          <div className="min-w-0">
            {/* Evidence → career path journey, played step by step */}
            <JourneySteps />

            <div className="mt-[18px] border-t border-[#f0ece5] pt-4">
              <p className="font-editorial text-[22px] font-semibold leading-[1.2]">
                The smart way <em className="text-brand-blue">to move forward.</em>
              </p>
              <p className="mt-1.5 text-sm text-[#5c5a55]">We bring everything together and show you the right steps.</p>
              <ul className="mt-3.5 flex flex-wrap gap-2 text-[13.5px] font-bold">
                {benefits.map(({ label, tone }) => (
                  <li key={label} className={`rounded-full px-3 py-[7px] ${tone}`}>
                    {label}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
