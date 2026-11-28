import type { ReactNode } from "react";

import type { ApplicationStatus, CompanyStatus, JobState } from "@/lib/jobs";

// Small building blocks shared by the company portal, the admin's Companies page and Market Pulse's Jobs view.
// Class names are written out in full so Tailwind finds them.

const pillTones = {
  green: "bg-[#dcf5e3] text-[#14592f]",
  amber: "bg-[#ffefc7] text-[#6e4500]",
  grey: "bg-[#ebe9e3] text-[#46433c]",
  red: "bg-[#f7e0e0] text-[#842a2a]",
  lime: "bg-[#d0ffa4] text-[#1f3a00]",
  blue: "bg-[#e3ecff] text-[#1e3a8a]",
  purple: "bg-[#efe8ff] text-[#3d24b8]",
} as const;

export type Tone = keyof typeof pillTones;

export function Pill({ tone, children, className = "" }: { tone: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-bold ${pillTones[tone]} ${className}`}>
      {children}
    </span>
  );
}

export const JOB_STATE: Record<JobState, { label: string; tone: Tone }> = {
  DRAFT: { label: "Draft", tone: "grey" },
  WAITING: { label: "Waiting for verification", tone: "amber" },
  HIDDEN: { label: "Hidden: company not approved", tone: "red" },
  LIVE: { label: "Live", tone: "green" },
  EXPIRED: { label: "Closing date passed", tone: "red" },
  CLOSED: { label: "Closed", tone: "red" },
};

export const COMPANY_STATUS: Record<CompanyStatus, { label: string; tone: Tone }> = {
  PENDING: { label: "Waiting for verification", tone: "amber" },
  VERIFIED: { label: "Verified company", tone: "lime" },
  REJECTED: { label: "Not approved", tone: "red" },
};

/** An application's status, as the company sees it and as the student sees it. */
export const APPLICATION_STATUS: Record<ApplicationStatus, { company: string; student: string; tone: Tone; studentTone: Tone }> = {
  NEW: { company: "New", student: "Sent", tone: "lime", studentTone: "grey" },
  SEEN: { company: "Seen", student: "Seen by the company", tone: "blue", studentTone: "blue" },
  SHORTLISTED: { company: "Shortlisted", student: "Shortlisted", tone: "purple", studentTone: "purple" },
  NOT_SELECTED: { company: "Not selected", student: "Not selected", tone: "red", studentTone: "red" },
};

const avatarColors = ["bg-[#5b3df5]", "bg-[#0b7a6d]", "bg-[#c2185b]", "bg-[#2f7a22]", "bg-[#a65a0b]", "bg-[#2f6fd9]", "bg-[#7a3fd1]", "bg-[#0f766e]"];

export function initialsOf(name: string): string {
  return (
    name
      .split(/\s+/)
      .filter((w) => /[A-Za-z0-9]/.test(w))
      .slice(0, 2)
      .map((w) => w[0]!.toUpperCase())
      .join("") || "?"
  );
}

/** A coloured square with a name's initials; the colour follows the id, so it stays the same everywhere. */
export function Avatar({ name, id, size = "md" }: { name: string; id: string; size?: "sm" | "md" | "lg" }) {
  let hash = 0;
  for (const ch of id) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  const sizes = { sm: "size-8 rounded-[10px] text-xs", md: "size-10 rounded-xl text-sm", lg: "size-14 rounded-2xl text-lg" };
  return (
    <span aria-hidden="true" className={`grid shrink-0 place-items-center font-extrabold text-white ${sizes[size]} ${avatarColors[hash % avatarColors.length]}`}>
      {initialsOf(name)}
    </span>
  );
}

export function SkillChip({ name, preferred = false }: { name: string; preferred?: boolean }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-[12.5px] font-semibold leading-tight ${
        preferred ? "border border-dashed border-[#a39b8b] bg-white text-[#46433c]" : "bg-[#efe8ff] text-[#3d24b8]"
      }`}
    >
      {name}
    </span>
  );
}

export function MetaChip({ children }: { children: ReactNode }) {
  return <span className="inline-flex items-center rounded-full bg-[#f4f2ee] px-2.5 py-1 text-[12.5px] font-semibold text-[#3b3845]">{children}</span>;
}

export function plural(n: number, one: string, many = `${one}s`): string {
  return `${n} ${n === 1 ? one : many}`;
}
