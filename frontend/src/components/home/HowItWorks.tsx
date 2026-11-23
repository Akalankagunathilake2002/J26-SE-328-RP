import Image from "next/image";
import Link from "next/link";

import { ArrowRightIcon } from "@/components/icons";

type Card = {
  id: string;
  eyebrow?: string;
  title: string;
  text: string;
  href: string;
  linkLabel: string;
  image: { src: string; alt: string; width: number; height: number };
  /** Which part of the photo stays in view (object-position). */
  art: string;
  /** Colour of the eyebrow and the link. */
  accent: string;
  /** Tilt that fans the cards out (two or more columns only). */
  tilt: string;
};

const cards: Card[] = [
  {
    id: "industry",
    eyebrow: "Industry intelligence",
    title: "Know what the industry needs.",
    text: "Explore real market signals to understand emerging roles, in-demand skills, and salary trends",
    href: "/market-pulse",
    linkLabel: "Explore industry",
    image: {
      src: "/photos/industry.jpg",
      alt: "A young woman analysing charts and notes at her laptop",
      width: 1000,
      height: 666,
    },
    art: "object-[50%_40%]",
    accent: "text-[#4a2fd0]",
    tilt: "sm:-rotate-3 sm:translate-y-3",
  },
  {
    id: "prove",
    title: "Prove what you can do",
    text: "Turn your projects, academic work, certificates, CV, and experience into a clear, evidence-backed skill profile",
    href: "/skills-profile",
    linkLabel: "Explore",
    image: {
      src: "/photos/evidence.jpg",
      alt: "A graduate holding a rolled diploma tied with a red ribbon",
      width: 1000,
      height: 668,
    },
    art: "object-[60%_50%]",
    accent: "text-[#8a5a00]",
    tilt: "sm:-rotate-1",
  },
  {
    id: "stand",
    title: "See where you stand",
    text: "Understand your career readiness and discover where you can improve",
    href: "/skill-analysis",
    linkLabel: "Explore",
    image: {
      src: "/photos/stand.jpg",
      alt: "Two students reviewing their work together on a laptop",
      width: 1000,
      height: 666,
    },
    art: "object-[50%_50%]",
    accent: "text-[#a3135a]",
    tilt: "sm:rotate-1",
  },
  {
    id: "practice",
    title: "Practice. Learn. Grow.",
    text: "Follow personalized learning recommendations and practice with AI-powered mock interviews to build career confidence",
    href: "/mock-interview",
    linkLabel: "Explore",
    image: {
      src: "/photos/practice.jpg",
      alt: "A candidate in an online job interview over a video call",
      width: 1000,
      height: 668,
    },
    art: "object-[50%_40%]",
    accent: "text-[#146c3d]",
    tilt: "sm:rotate-3 sm:translate-y-3",
  },
];

/** The four features as a fan of cards: one row on wide screens, two columns on tablets, a stack on phones. */
export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      aria-labelledby="how-it-works-heading"
      className="mx-auto max-w-[1240px] scroll-mt-32 px-4 pb-4 pt-11 sm:px-8 lg:scroll-mt-24"
    >
      <h2
        id="how-it-works-heading"
        className="mb-[22px] text-center text-[13.5px] font-extrabold uppercase tracking-[0.12em] text-[#5b3df5]"
      >
        How it works
      </h2>
      {/* max-[1060px] keeps the two-column rule off wide screens: Tailwind puts the min-[1060px] rule before sm:. */}
      <div className="grid grid-cols-1 items-start gap-[18px] sm:max-[1060px]:grid-cols-2 min-[1060px]:grid-cols-4">
        {cards.map((card) => (
          <FeatureCard key={card.id} card={card} />
        ))}
      </div>
    </section>
  );
}

function FeatureCard({ card }: { card: Card }) {
  const headingId = `${card.id}-heading`;
  return (
    <article
      aria-labelledby={headingId}
      className={`flex flex-col overflow-hidden rounded-[22px] bg-white shadow-[0_22px_44px_-26px_rgba(40,30,10,0.5)] transition-transform duration-200 motion-reduce:transition-none sm:hover:translate-y-0 sm:hover:rotate-0 ${card.tilt}`}
    >
      {/* Real photo filling the top of the card; it zooms in a little on hover. */}
      <div className="group/photo relative h-[230px] overflow-hidden bg-[#e9e6df]">
        <Image
          src={card.image.src}
          alt={card.image.alt}
          fill
          sizes="(min-width: 1060px) 300px, (min-width: 640px) 50vw, 100vw"
          className={`object-cover transition-transform duration-700 ease-out group-hover/photo:scale-105 motion-reduce:transition-none ${card.art}`}
        />
      </div>
      <div className="flex flex-1 flex-col gap-2 px-5 pb-5 pt-[18px]">
        {card.eyebrow && (
          <p className={`text-xs font-extrabold uppercase tracking-[0.08em] ${card.accent}`}>{card.eyebrow}</p>
        )}
        <h3 id={headingId} className="font-editorial text-2xl font-semibold leading-[1.15]">
          {card.title}
        </h3>
        <p className="text-[15px] text-[#5c5a55]">{card.text}</p>
        <Link
          href={card.href}
          className={`mt-auto inline-flex min-h-11 items-center gap-1.5 self-start font-extrabold hover:underline ${card.accent}`}
        >
          {card.linkLabel}
          <span className="sr-only">: {card.title}</span>
          <ArrowRightIcon className="size-4" strokeWidth={2.4} />
        </Link>
      </div>
    </article>
  );
}
