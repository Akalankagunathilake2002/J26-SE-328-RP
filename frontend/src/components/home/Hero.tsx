import Image from "next/image";
import Link from "next/link";

import {
  ArrowRightIcon,
  ArrowUpRightIcon,
  BookIcon,
  MessageIcon,
  SparkleDoodle,
  SquiggleDoodle,
  StarIcon,
  TargetIcon,
  TrendingUpIcon,
  UserIcon,
} from "@/components/icons";

const journey = [
  { label: "Your Evidence", labelX: 47, dotX: 56, dot: "bg-pink" },
  { label: "Your Skills", labelX: 180, dotX: 201, dot: "bg-brand-blue" },
  { label: "Industry Demand", labelX: 292, dotX: 347, dot: "bg-lime", star: true },
  { label: "Your Career Path", labelX: 442, dotX: 495, dot: "bg-lime" },
];

const benefits = [
  { label: "Know what's in demand", Icon: TrendingUpIcon },
  { label: "Understand your strengths", Icon: UserIcon },
  { label: "Identify skill gaps", Icon: TargetIcon },
  { label: "Learn what matters", Icon: BookIcon },
  { label: "Practice & get feedback", Icon: MessageIcon },
];

export function Hero() {
  return (
    <section className="hero-grid relative overflow-hidden border-b-[3px] border-ink">
      {/* Bookmark ribbon */}
      <span
        aria-hidden="true"
        className="absolute left-5 top-0 h-[60px] w-[53px] bg-white [clip-path:polygon(0_0,100%_0,100%_100%,50%_68%,0_100%)]"
      />

      <div className="mx-auto flex max-w-[1440px] flex-col items-center gap-12 px-5 pb-16 pt-24 lg:h-[728px] lg:flex-row lg:items-start lg:justify-between lg:gap-8 lg:pb-0 lg:pl-[72px] lg:pr-[92px] lg:pt-[153px]">
        <div className="w-full max-w-[600px]">
          <div className="flex items-center gap-5">
            <p className="border-2 border-ink bg-pink px-[15px] py-[2px] font-condensed text-[17px] font-semibold uppercase leading-[23px] tracking-[0.01em]">
              AI-Powered Career Readiness Platform
            </p>
            <SquiggleDoodle className="w-[30px] text-lime" />
          </div>

          <h1 className="mt-[18px] font-display text-[40px] uppercase leading-[1.15] text-white text-block-shadow sm:text-[48px] lg:text-[46px] lg:leading-[68px] xl:text-[53px]">
            <span className="block">Bridge what</span>
            <span className="block">you know</span>
            <span className="block text-[#ffe030]">with what</span>
            <span className="block text-[#ffe030]">industry needs.</span>
          </h1>

          <p className="mt-[25px] max-w-[460px] text-[18px] font-medium leading-[27px] text-white">
            Understand your skills, discover the gaps, and get a personalized path to become career
            ready.
          </p>

          <Link
            href="#how-it-works"
            className="hard-shadow mt-[22px] inline-flex h-[56px] items-center gap-3 bg-lime px-[30px] text-[20px] font-medium transition-transform hover:-translate-y-0.5"
          >
            Explore How It Works
            <ArrowRightIcon className="size-5" />
          </Link>
        </div>

        <HeroVisual />
      </div>
    </section>
  );
}

/** Students above the "smart way" card. Drawn at desktop size and scaled down on smaller screens. */
function HeroVisual() {
  return (
    <div className="hero-visual relative shrink-0 lg:-mt-[46px]">
      <div className="absolute left-0 top-0 h-[575px] w-[612px] origin-top-left scale-(--visual-scale)">
        <Image
          src="/illustrations/hero-students.png"
          alt="Four students with a book, a tablet, a laptop and a coffee cup"
          width={547}
          height={249}
          className="absolute left-[14px] top-0"
          loading="eager"
        />

        {/* Stacked paper layers behind the card */}
        <div className="absolute left-[42px] top-[309px] h-[266px] w-[541px] bg-ink" />
        <div className="absolute left-[31px] top-[296px] h-[266px] w-[540px] border-[2.5px] border-ink bg-cyan" />

        <div className="absolute left-0 top-[251px] h-[300px] w-[553px] border-[2.5px] border-ink bg-cream">
          {/* Notebook binding dots */}
          <div className="absolute left-[12px] top-[20px] flex flex-col gap-[17.4px]">
            {Array.from({ length: 8 }, (_, i) => (
              <span key={i} className="size-[8.6px] rounded-full bg-ink" />
            ))}
          </div>

          {/* Evidence → career path journey */}
          <ol>
            {journey.map((step) => (
              <li key={step.label}>
                <span
                  className="absolute top-[21px] whitespace-nowrap text-[11px] font-semibold"
                  style={{ left: step.labelX }}
                >
                  {step.label}
                </span>
                <span
                  className={`absolute top-[59px] z-10 grid -translate-x-1/2 place-items-center rounded-full border-2 border-ink ${step.dot} ${step.star ? "size-[22px]" : "size-[17px]"}`}
                  style={{ left: step.dotX }}
                >
                  {step.star && <StarIcon className="size-3" strokeWidth={2.5} />}
                </span>
              </li>
            ))}
          </ol>
          <span className="absolute left-[56px] top-[67px] h-[2px] w-[439px] bg-ink" />

          <div className="absolute left-[47px] top-[110px] w-[225px]">
            <p className="text-[19px] font-semibold leading-[27px]">
              The smart way
              <br />
              <span className="text-brand-blue">to move forward.</span>
            </p>
            <p className="mt-[13px] text-[13.5px] leading-[18px] text-muted">
              We bring everything together and show you the right steps.
            </p>
            <ArrowUpRightIcon className="mt-[22px] ml-[7px] size-[18px] text-brand-blue" />
          </div>

          <ul className="absolute left-[292px] top-[98px] flex h-[177px] w-[237px] flex-col gap-[10px] border-[2.5px] border-ink bg-periwinkle px-[13px] pt-[14px] text-[14px] font-semibold leading-[18px] text-white shadow-[5px_6px_0_var(--color-ink)]">
            {benefits.map(({ label, Icon }) => (
              <li key={label} className="flex items-start gap-[13px]">
                <Icon className="mt-px size-[17px] shrink-0" />
                <span className="w-[165px]">{label}</span>
              </li>
            ))}
          </ul>
        </div>

        <SparkleDoodle className="absolute left-[578px] top-[514px] w-[34px] text-lime" />
      </div>
    </div>
  );
}
