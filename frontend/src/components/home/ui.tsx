import Link from "next/link";
import type { ReactNode } from "react";

import { ChevronCircleIcon, SquiggleDoodle } from "@/components/icons";

export function ExploreButton({ href, children = "Explore" }: { href: string; children?: ReactNode }) {
  return (
    <Link
      href={href}
      className="inline-flex h-[64px] w-[271px] max-w-full items-center justify-center gap-[10px] border-2 border-ink bg-butter text-[19.5px] font-bold uppercase tracking-[0.02em] shadow-[4px_5px_0_var(--color-ink)] transition-transform hover:-translate-y-0.5"
    >
      {children}
      <ChevronCircleIcon className="size-[22px]" strokeWidth={1.75} />
    </Link>
  );
}

export function SectionTag({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-center gap-[18px]">
      <p className="border-2 border-ink bg-sun px-[11px] font-condensed text-[18px] font-semibold uppercase leading-[27px] shadow-[2px_2px_0_var(--color-ink)]">
        {children}
      </p>
      <SquiggleDoodle className="w-[30px] text-sun" />
    </div>
  );
}

/** Outlined heading used by the feature sections. */
export function SectionHeading({ children }: { children: ReactNode }) {
  return (
    <h2 className="font-display text-[34px] uppercase leading-[1.2] text-outline-shadow sm:text-[44px] lg:text-[52px] lg:leading-[68px]">
      {children}
    </h2>
  );
}

/** Large body copy used by the feature sections. */
export function SectionText({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <p className={`text-[22px] leading-[1.6] text-[#1e1e1e] lg:text-[36px] lg:leading-[54px] ${className}`}>
      {children}
    </p>
  );
}
