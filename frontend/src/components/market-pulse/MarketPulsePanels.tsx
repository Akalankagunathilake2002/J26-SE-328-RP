import {
  BookOpen,
  Code,
  GraduationCap,
  Info,
  Languages,
  TrendingDown,
  Users,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { ChevronCircleIcon } from "@/components/icons";
import type { RoleProfile, Selection, SkillDemand, Source } from "@/lib/marketPulse";

// Background colours are added per card: a shared bg-white would override them.
const card = "border-2 border-ink shadow-[7px_7px_0_var(--color-ink)]";
const TOP_SKILLS = 8;
const SMALL_SAMPLE = 10; // fewer ads with text than this: percentages are only indicative

const categoryIcons: Record<string, LucideIcon> = {
  Technical: Code,
  Tool: Wrench,
  "Domain knowledge": BookOpen,
  "Soft skill": Users,
  Language: Languages,
  Qualification: GraduationCap,
};

/** The person card next to the filters, labelled with the selected role. */
export function RoleCard({ label }: { label: string }) {
  return (
    <div className="relative size-[170px] shrink-0">
      <div className={`${card} flex size-full items-end justify-center overflow-hidden bg-white`}>
        <svg viewBox="0 0 120 110" aria-hidden="true" className="w-[78%] text-periwinkle">
          <circle cx="60" cy="40" r="22" fill="currentColor" stroke="var(--color-ink)" strokeWidth="3" />
          <path d="M16 112c0-30 20-44 44-44s44 14 44 44Z" fill="currentColor" stroke="var(--color-ink)" strokeWidth="3" />
        </svg>
      </div>
      <p className="absolute -bottom-3 -right-4 max-w-[220px] border-2 border-ink bg-white px-2 py-0.5 font-mono text-[12px] shadow-[2px_2px_0_var(--color-ink)]">
        {label}
      </p>
    </div>
  );
}

/** Ads, experience and seniority behind the selected role. */
export function RoleSummary({ role }: { role: RoleProfile }) {
  return (
    <dl className="mt-4 grid gap-1 text-[13px] text-muted">
      <div>
        <dt className="inline font-semibold text-ink">Experience asked: </dt>
        <dd className="inline">{formatCounts(role.experience)}</dd>
      </div>
      <div>
        <dt className="inline font-semibold text-ink">Seniority: </dt>
        <dd className="inline">{formatCounts(role.seniority)}</dd>
      </div>
      <div>
        <dt className="inline font-semibold text-ink">Job titles: </dt>
        <dd className="inline">{role.titles.join("; ")}</dd>
      </div>
    </dl>
  );
}

export type Stat = { label: string; value: string; Icon: LucideIcon; tone: string; detail?: string };

export function StatCards({ stats }: { stats: Stat[] }) {
  return (
    <ul className="grid grid-cols-2 gap-5 lg:grid-cols-4">
      {stats.map(({ label, value, Icon, tone, detail }) => (
        <li key={label} className={`${card} ${tone} flex min-h-[112px] flex-col justify-between gap-3 p-4`}>
          <div className="flex items-start justify-between gap-2">
            <p className="text-[12px] font-bold uppercase leading-[1.3] tracking-[0.02em]">{label}</p>
            <span className="grid size-7 shrink-0 place-items-center rounded-[5px] border-2 border-ink bg-white">
              <Icon className="size-4" aria-hidden="true" />
            </span>
          </div>
          <div>
            <p className="text-[32px] font-bold leading-none tracking-[-0.01em]">{value}</p>
            {detail && <p className="mt-1 text-[12px] text-ink/70">{detail}</p>}
          </div>
        </li>
      ))}
    </ul>
  );
}

export function DataSourcesCard({ sources }: { sources: Source[] }) {
  return (
    <section className={`${card} bg-white p-5`}>
      <h2 className="text-[22px] font-bold">Data sources</h2>
      <p className="text-[13px] text-muted">Sri Lankan job sites and what is collected from them</p>

      <table className="mt-4 w-full border-2 border-ink text-[14px]">
        <thead className="bg-periwinkle text-[12px] uppercase text-white">
          <tr>
            <th scope="col" className="px-3 py-2 text-left font-bold">Source</th>
            <th scope="col" className="px-3 py-2 text-right font-bold">Collected</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((source) => (
            <tr key={source.site} className="border-t-2 border-ink">
              <td className="px-3 py-3">
                <span className="flex items-center gap-2 font-semibold">
                  <span
                    aria-hidden="true"
                    className={`size-2.5 shrink-0 rounded-full border border-ink ${source.collected ? "bg-green-500" : "bg-red-500"}`}
                  />
                  <a href={source.url} target="_blank" rel="noreferrer" className="underline-offset-4 hover:underline">
                    {source.name}
                  </a>
                </span>
                {!source.collected && (
                  <span className="mt-0.5 block pl-[18px] text-[12px] text-muted" title={source.reason ?? undefined}>
                    Not allowed by the site&apos;s terms
                  </span>
                )}
              </td>
              <td className="px-3 py-3 text-right font-bold">
                {source.collected ? source.ads.toLocaleString("en") : <span className="font-normal text-muted">No</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="mt-5 flex gap-2 rounded-[8px] border-2 border-ink bg-peach p-3 text-[13px] leading-[1.5]">
        <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        New ads are added when a collection run is started. Automatic daily syncing is coming soon.
      </p>

      <div className="mt-6 flex justify-center">
        <Link
          href="/skills-profile"
          className="inline-flex h-11 items-center gap-2 border-2 border-ink bg-butter px-6 text-[15px] font-bold shadow-[3px_4px_0_var(--color-ink)] transition-transform hover:-translate-y-0.5"
        >
          Skills page
          <ChevronCircleIcon className="size-5" strokeWidth={1.75} />
        </Link>
      </div>
    </section>
  );
}

export function TopSkillsCard({ selection }: { selection: Selection }) {
  const skills = selection.skills.slice(0, TOP_SKILLS);
  return (
    <section className={`${card} bg-white p-5`}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <CardTitle>Top skills demand</CardTitle>
        <p className="text-[13px] text-muted">
          {selection.label} · {plural(selection.ads, "ad")}
        </p>
      </div>

      {skills.length > 0 ? (
        <ul className="mt-4 space-y-3">
          {skills.map((skill) => (
            <SkillBar key={skill.skill} skill={skill} adsWithText={selection.adsWithText} />
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-[14px] text-muted">
          {selection.ads === 0
            ? `No ads collected for ${selection.sector?.sector ?? "this selection"} yet.`
            : "No skills could be read from these ads (their flyers have no readable requirements)."}
        </p>
      )}

      {selection.adsWithText > 0 && selection.adsWithText < SMALL_SAMPLE && (
        <p className="mt-4 text-[12px] text-muted">
          Based on {plural(selection.adsWithText, "ad")} with readable text, so the percentages are only indicative.
          They become reliable as more ads are collected.
        </p>
      )}
    </section>
  );
}

function SkillBar({ skill, adsWithText }: { skill: SkillDemand; adsWithText: number }) {
  const Icon = categoryIcons[skill.category] ?? BookOpen;
  const percent = Math.round(skill.share * 100);
  return (
    <li className="flex items-center gap-3">
      <span
        title={skill.category}
        className="grid size-8 shrink-0 place-items-center rounded-[6px] border-2 border-ink bg-periwinkle text-white"
      >
        <Icon className="size-4" aria-hidden="true" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-3 text-[13px] font-semibold uppercase">
          <span className="truncate">{skill.skill}</span>
          <span className="shrink-0 text-brand-blue">{percent}%</span>
        </div>
        <div aria-hidden="true" className="mt-1 h-2.5 rounded-full border-2 border-ink bg-page">
          <div className="h-full rounded-full bg-lime" style={{ width: `${percent}%` }} />
        </div>
        <p className="mt-0.5 text-[11px] text-muted">
          {skill.ads} of {plural(adsWithText, "ad")} · {skill.category}
        </p>
      </div>
    </li>
  );
}

/** Needs ads collected over time, which the daily sync will provide. */
export function DeadSkillsCard() {
  return (
    <section className={`${card} bg-white p-5`}>
      <CardTitle>Dead skills</CardTitle>
      <p className="mt-4 flex gap-3 rounded-[8px] border-2 border-dashed border-ink/40 p-4 text-[14px] leading-[1.5] text-muted">
        <TrendingDown className="mt-0.5 size-5 shrink-0" aria-hidden="true" />
        Skills that job ads ask for less and less over time. Shown once ads have been collected over several weeks.
      </p>
    </section>
  );
}

export function Notice({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className={`${card} mt-10 bg-cream p-6`}>
      <h2 className="text-[22px] font-bold">{title}</h2>
      <div className="mt-2 text-[15px] leading-[1.6]">{children}</div>
    </section>
  );
}

function CardTitle({ children }: { children: ReactNode }) {
  return <h2 className="font-mono text-[16px] font-bold uppercase tracking-[0.06em]">{children}</h2>;
}

function formatCounts(counts: Record<string, number>): string {
  return Object.entries(counts)
    .map(([label, count]) => `${label} (${count})`)
    .join(", ");
}

export function plural(count: number, word: string): string {
  return `${count.toLocaleString("en")} ${word}${count === 1 ? "" : "s"}`;
}
