import Image from "next/image";
import type { ReactNode } from "react";

import { ExploreButton, SectionHeading, SectionTag, SectionText } from "./ui";

/** Dashed frame shared by the industry and "see where you stand" sections. */
function DashedFrame({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`relative mx-auto max-w-[1325px] border-2 border-dashed border-ink ${className}`}>
      {children}
    </div>
  );
}

export function IndustrySection() {
  return (
    <section id="how-it-works" aria-labelledby="industry-heading" className="scroll-mt-6 px-4 pt-12 lg:px-0 lg:pt-[47px]">
      <DashedFrame className="px-5 pt-12 lg:h-[907px] lg:px-[60px] lg:pt-[139px]">
        <div className="relative z-10">
          <div className="lg:ml-2">
            <SectionTag>Industry intelligence</SectionTag>
          </div>
          <div id="industry-heading" className="mt-6 lg:mt-[34px]">
            <SectionHeading>
              <span className="block">Know what</span>
              <span className="block">the industry</span>
              <span className="block">needs.</span>
            </SectionHeading>
          </div>
          <SectionText className="mt-6 lg:-ml-[7px] lg:mt-[41px]">
            <span className="lg:block">Explore real market signals to</span>{" "}
            <span className="lg:block">understand emerging roles,</span>{" "}
            <span className="lg:block">in-demand skills,</span>{" "}
            <span className="lg:block">and salary trends</span>
          </SectionText>
          <div className="mt-8 lg:mt-[27px]">
            <ExploreButton href="/market-pulse">Explore industry</ExploreButton>
          </div>
        </div>

        <Image
          src="/illustrations/industry.png"
          alt="A student pointing at market cards for in-demand skills, salary trends and emerging roles"
          width={700}
          height={803}
          sizes="(min-width: 1024px) 700px, 100vw"
          className="mx-auto mt-10 w-full max-w-[560px] lg:absolute lg:-bottom-[103px] lg:-right-[26px] lg:mt-0 lg:w-[700px] lg:max-w-none"
        />
      </DashedFrame>
    </section>
  );
}

export function ProveSection() {
  return (
    <section aria-labelledby="prove-heading" className="px-4 pt-16 lg:px-0 lg:pt-[90px]">
      <div className="relative mx-auto max-w-[1325px] pt-[60px] lg:h-[856px] lg:pt-[115px]">
        <div className="relative lg:ml-[33px] lg:h-[703px] lg:w-[1242px]">
          <FolderBack />
          {/* Yellow sheet and shadow peeking out under the folder */}
          <div className="absolute -bottom-[21px] -right-[21px] left-[30px] top-[28px] rounded-[30px] border-4 border-ink bg-[#fde144] shadow-[12px_13px_0_var(--color-ink)]" />
          <BurstLines className="absolute -left-[62px] -top-[40px] hidden w-[72px] lg:block" />

          <div className="relative flex flex-col-reverse gap-8 rounded-[30px] border-4 border-ink bg-lavender px-5 pb-10 pt-10 lg:block lg:h-full lg:p-0">
            <Image
              src="/illustrations/evidence-stack.png"
              alt="Evidence cards for projects, certificates, academic work and work experience, clipped together into a skill profile with an 86% confidence score"
              width={351}
              height={731}
              sizes="(min-width: 1024px) 351px, 70vw"
              className="mx-auto w-[70%] max-w-[351px] lg:absolute lg:left-[105px] lg:top-[27px] lg:w-[351px]"
            />
            <div className="lg:absolute lg:left-[595px] lg:top-[95px]">
              <h2 id="prove-heading" className="font-display text-[34px] uppercase leading-[1.2] text-outline-shadow sm:text-[44px] lg:text-[52px] lg:leading-[68px]">
                <span className="block">Prove what</span>
                <span className="block">you can do</span>
              </h2>
              <SectionText className="mt-6 max-w-[520px] lg:mt-[75px]">
                <span className="lg:block">Turn your projects, academic</span>{" "}
                <span className="lg:block">work, certificates, CV, and</span>{" "}
                <span className="lg:block">experience into a clear,</span>{" "}
                <span className="lg:block">evidence-backed skill profile</span>
              </SectionText>
              <div className="mt-8 lg:ml-[10px] lg:mt-[6px]">
                <ExploreButton href="/skills-profile" />
              </div>
            </div>
          </div>

          <Paperclip className="absolute -top-[80px] right-[42px] hidden w-[112px] lg:block" />
        </div>
      </div>
    </section>
  );
}

export function StandSection() {
  return (
    <section aria-labelledby="stand-heading" className="px-4 pt-20 lg:px-0 lg:pt-[119px]">
      <DashedFrame className="px-5 pt-12 lg:h-[906px] lg:px-[55px] lg:pt-[125px]">
        <Checkerboard className="absolute -right-[8px] -top-[6px] hidden lg:grid" />
        <div className="relative z-10">
          <div id="stand-heading">
            <SectionHeading>
              <span className="block">See where</span>
              <span className="block">you stand</span>
            </SectionHeading>
          </div>
          <SectionText className="mt-6 lg:-ml-[3px] lg:mt-[89px]">
            <span className="lg:block">Understand your career</span>{" "}
            <span className="lg:block">readiness and discover where</span>{" "}
            <span className="lg:block">you can improve</span>
          </SectionText>
          <div className="mt-8 lg:ml-[1px] lg:mt-[116px]">
            <ExploreButton href="/skill-analysis" />
          </div>
        </div>

        <Image
          src="/illustrations/students-stand.png"
          alt="Two students looking at their results on a tablet"
          width={806}
          height={601}
          sizes="(min-width: 1024px) 806px, 100vw"
          className="mx-auto mt-10 w-full max-w-[640px] lg:absolute lg:-bottom-[113px] lg:right-[18px] lg:mt-0 lg:w-[806px] lg:max-w-none"
        />
      </DashedFrame>
    </section>
  );
}

export function PracticeSection() {
  return (
    <section aria-labelledby="practice-heading" className="px-4 pt-20 lg:px-0 lg:pt-[166px]">
      <div className="relative mx-auto max-w-[1325px] border-2 border-dashed border-ink px-4 pb-[100px] pt-8 sm:pb-[130px] lg:h-[1423px] lg:p-0">
        <div className="relative rounded-l-[48px] bg-sun px-6 pb-[280px] pt-12 shadow-[18px_17px_0_var(--color-ink)] sm:pb-[420px] lg:absolute lg:left-[316px] lg:top-[54px] lg:h-[1148px] lg:w-[970px] lg:rounded-l-[72px] lg:p-0 lg:shadow-[36px_34px_0_var(--color-ink)]">
          <DotColumn className="absolute right-[93px] top-[58px] hidden lg:flex" />

          <div className="lg:absolute lg:right-[245px] lg:top-[128px]">
            <h2 id="practice-heading" className="font-script text-[52px] uppercase leading-[1.1] tracking-[0.02em] text-outline lg:text-right lg:text-[78px] lg:leading-[66px]">
              <span className="block">Practice</span>
              <span className="block">Learn</span>
              <span className="block">Grow</span>
            </h2>
          </div>

          <SectionText className="mt-8 lg:absolute lg:left-[220px] lg:top-[354px] lg:mt-0">
            <span className="lg:block">Follow personalized learning</span>{" "}
            <span className="lg:block">recommendations and</span>{" "}
            <span className="lg:block">practice with AI-powered</span>{" "}
            <span className="lg:block">mock interviews to build</span>{" "}
            <span className="lg:block">career confidence</span>
          </SectionText>

          <div className="mt-10 lg:absolute lg:left-[465px] lg:top-[656px] lg:mt-0">
            <ExploreButton href="/mock-interview" />
          </div>

          <Image
            src="/illustrations/ai-interview.png"
            alt="A student in a mock interview with a friendly AI interviewer wearing headphones"
            width={813}
            height={529}
            sizes="(min-width: 1024px) 813px, 100vw"
            className="absolute -bottom-[80px] left-[-10px] w-[110%] max-w-[813px] sm:-bottom-[110px] lg:-bottom-[155px] lg:-left-[284px] lg:w-[813px] lg:max-w-none"
          />
        </div>
      </div>
    </section>
  );
}

function FolderBack() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 1242 140"
      preserveAspectRatio="none"
      className="absolute -top-[115px] left-0 hidden h-[140px] w-full lg:block"
    >
      <path
        d="M25 140 V30 Q25 2 55 2 H480 Q500 2 512 18 L548 54 Q558 62 575 62 H1205 Q1222 62 1222 80 V140 Z"
        fill="#9e80fc"
        stroke="#0d0d0d"
        strokeWidth="4"
        vectorEffect="non-scaling-stroke"
      />
      <path d="M48 140 V100 Q48 80 70 80 H500 Q515 80 525 92 L565 140 Z" fill="#0d0d0d" />
    </svg>
  );
}

function BurstLines({ className = "" }: { className?: string }) {
  const lines = ["M44 8 L56 30", "M10 40 L34 54", "M8 92 L36 86"];
  return (
    <svg aria-hidden="true" viewBox="0 0 72 112" fill="none" strokeLinecap="round" className={className}>
      {lines.map((d) => (
        <g key={d}>
          <path d={d} stroke="#0d0d0d" strokeWidth="17" />
          <path d={d} stroke="#ffe03a" strokeWidth="10" />
        </g>
      ))}
    </svg>
  );
}

function Paperclip({ className = "" }: { className?: string }) {
  const d = "M40 172 V48 a26 26 0 0 1 52 0 V150 a40 40 0 0 1 -80 0 V60";
  return (
    <svg aria-hidden="true" viewBox="0 0 104 204" fill="none" strokeLinecap="round" className={`-rotate-[14deg] ${className}`}>
      <path d={d} stroke="#0d0d0d" strokeWidth="15" />
      <path d={d} stroke="#ffffff" strokeWidth="8" />
    </svg>
  );
}

function Checkerboard({ className = "" }: { className?: string }) {
  // 4×4 grid read row by row: p = pink, c = peach, . = empty.
  const cells = ".pcp" + "pcpc" + ".pcp" + "p...";
  const tone = { p: "bg-pink", c: "bg-peach", ".": "" } as const;
  return (
    <div aria-hidden="true" className={`grid grid-cols-[repeat(4,77px)] grid-rows-[repeat(4,77px)] ${className}`}>
      {[...cells].map((cell, i) => (
        <span key={i} className={tone[cell as keyof typeof tone]} />
      ))}
    </div>
  );
}

function DotColumn({ className = "" }: { className?: string }) {
  return (
    <div aria-hidden="true" className={`flex-col gap-[27.5px] ${className}`}>
      {Array.from({ length: 24 }, (_, i) => (
        <span key={i} className="size-[14.5px] rounded-full bg-white" />
      ))}
    </div>
  );
}
