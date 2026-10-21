import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

// Building blocks in the app's playful card style (as on the Skill Analysis page): white cards
// with a black border, rounded corners and a hard shadow, pastel tiles and lavender speech bubbles.

export const cardClass = "rounded-2xl border-2 border-ink bg-white shadow-[4px_4px_0px_#000]";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`${cardClass} p-5 sm:p-6 ${className}`}>{children}</section>;
}

/** A card heading with its icon; ``aside`` goes on the right (e.g. what the card shows). */
export function CardTitle({ Icon, children, aside }: { Icon: LucideIcon; children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
      <div className="flex items-center gap-2">
        <Icon className="size-5 text-ink" aria-hidden="true" />
        <h2 className="text-lg font-extrabold text-ink sm:text-xl">{children}</h2>
      </div>
      {aside && <div className="text-xs font-semibold text-ink/60">{aside}</div>}
    </div>
  );
}

export type StatTileProps = {
  label: string;
  value: string;
  Icon: LucideIcon;
  tone: string; // background class, e.g. "bg-lime"
  detail?: string;
};

export function StatTile({ label, value, Icon, tone, detail }: StatTileProps) {
  return (
    <div className={`${tone} flex min-h-[132px] flex-col justify-between gap-2 rounded-xl border-2 border-ink p-4 shadow-[3px_3px_0px_#000]`}>
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-bold leading-snug text-ink">{label}</span>
        <IconBox Icon={Icon} />
      </div>
      <span className="text-3xl font-black leading-none text-ink sm:text-4xl">{value}</span>
      {detail && <span className="truncate text-xs font-bold text-ink/70">{detail}</span>}
    </div>
  );
}

export function IconBox({ Icon, className = "bg-white" }: { Icon: LucideIcon; className?: string }) {
  return (
    <span className={`${className} flex size-7 shrink-0 items-center justify-center rounded-md border-2 border-ink shadow-[1px_1px_0px_#000]`}>
      <Icon className="size-3.5 text-ink" aria-hidden="true" />
    </span>
  );
}

/** A lavender speech bubble with its tail on the lower left. */
export function SpeechBubble({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`relative rounded-2xl border-2 border-ink bg-[#edddfc] px-4 py-2.5 shadow-[3px_3px_0px_#000] ${className}`}>
      <p className="text-xs font-bold leading-snug text-ink sm:text-sm">{children}</p>
      <span
        aria-hidden="true"
        className="absolute -bottom-2 left-6 size-3.5 -rotate-45 border-b-2 border-l-2 border-ink bg-[#edddfc]"
      />
    </div>
  );
}

export function Tag({ children, className = "bg-[#edddfc]" }: { children: ReactNode; className?: string }) {
  return (
    <span className={`${className} inline-block rounded-full border-2 border-ink px-3 py-0.5 text-xs font-bold uppercase tracking-wider text-ink shadow-[2px_2px_0px_#000]`}>
      {children}
    </span>
  );
}

export function Sparkle({ className = "" }: { className?: string }) {
  return (
    <span aria-hidden="true" className={`select-none text-sun ${className}`}>
      ✦
    </span>
  );
}

/** The yellow call-to-action button, as a link. */
export function ButtonLink({ href, children, className = "" }: { href: string; children: ReactNode; className?: string }) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center justify-center gap-2 rounded-xl border-2 border-ink bg-sun px-6 py-3 text-base font-black text-ink shadow-[3px_3px_0px_#000] transition-all hover:-translate-y-0.5 hover:bg-butter ${className}`}
    >
      {children}
    </Link>
  );
}
