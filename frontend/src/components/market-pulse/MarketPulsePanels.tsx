import {
  BookOpen,
  Briefcase,
  Clock,
  Code,
  Globe,
  GraduationCap,
  Info,
  Languages,
  Lightbulb,
  TrendingDown,
  TrendingUp,
  Users,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import Image from "next/image";
import type { ReactNode } from "react";

import { ChevronCircleIcon } from "@/components/icons";
import { ButtonLink, Card, CardTitle, IconBox, Sparkle, SpeechBubble } from "@/components/ui/playful";
import type { RoleProfile, Selection, SkillDemand, Source } from "@/lib/marketPulse";

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

/** Title, intro and the illustration with a speech bubble about the current selection. */
export function MarketPulseHero({ firstName, label }: { firstName: string; label?: string }) {
  const greeting = firstName ? `Hey, ${firstName}! ` : "";
  const about = label && label !== "All roles" ? `what ${label} ads ask for` : "what job ads are asking for";
  return (
    <section className="relative pt-4 sm:pt-6">
      <div className="grid grid-cols-1 items-end gap-6 md:grid-cols-[1.2fr_1fr] md:gap-4">
        <div className="z-10 pb-4 md:pb-10">
          <div className="relative inline-block">
            <Sparkle className="absolute -left-6 -top-2 text-2xl" />
            <h1 className="text-3xl font-extrabold leading-[1.1] tracking-tight text-ink sm:text-4xl lg:text-5xl">
              Market Pulse
            </h1>
          </div>
          <p className="mt-3 max-w-md text-sm font-medium leading-relaxed text-ink/75 sm:text-base">
            Track the skills job ads ask for, by job role and industry.
          </p>
        </div>

        {/* The bubble sits beside the illustration, inside this column, so it never covers the title. */}
        <div className="relative flex items-end justify-center gap-1 md:justify-end">
          <SpeechBubble className="z-20 mb-[45%] max-w-[190px] shrink sm:max-w-[220px]">
            {greeting}Here&apos;s {about} right now.
          </SpeechBubble>
          <div className="relative z-10 -mb-[2px] aspect-[1399/1605] w-[160px] shrink-0 sm:w-[200px]">
            <Image
              src="/illustrations/industry.png"
              alt="A student pointing at cards for in-demand skills, salary trends and emerging roles"
              fill
              priority
              sizes="200px"
              className="object-contain object-bottom"
            />
          </div>
        </div>
      </div>
    </section>
  );
}

/** The lime panel under the filters: what the selected role's ads ask for, or how to start. */
export function SelectionPanel({ role, roles, ads }: { role: RoleProfile | null; roles: number; ads: number }) {
  return (
    <div className="mt-5 rounded-xl border-2 border-ink bg-lime p-5 shadow-[2px_2px_0px_#000] sm:p-6">
      <div className="mb-3 flex items-center gap-3">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-full border-2 border-ink bg-white shadow-[1px_1px_0px_#000]">
          <Lightbulb className="size-4 fill-sun text-ink" aria-hidden="true" />
        </span>
        <h3 className="text-base font-extrabold text-ink sm:text-lg">
          {role ? `About ${role.role}` : `${plural(roles, "job role")} in ${plural(ads, "ad")}`}
        </h3>
      </div>
      {role ? (
        <dl className="grid gap-3">
          <PanelItem Icon={Clock} label="Experience asked" value={formatCounts(role.experience)} />
          <PanelItem Icon={Briefcase} label="Seniority" value={formatCounts(role.seniority)} />
          <PanelItem Icon={Users} label="Job titles" value={role.titles.join("; ")} />
        </dl>
      ) : (
        <p className="text-sm font-medium text-ink/80">
          Pick an industry and a job role, then apply the filters to see the skills its ads ask for.
        </p>
      )}
    </div>
  );
}

function PanelItem({ Icon, label, value }: { Icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="flex items-start gap-3">
      <IconBox Icon={Icon} className="mt-0.5 bg-[#edddfc]" />
      <div>
        <dt className="text-sm font-bold text-ink">{label}</dt>
        <dd className="text-xs font-medium text-ink/75">{value || "–"}</dd>
      </div>
    </div>
  );
}

export function TopSkillsCard({ selection }: { selection: Selection }) {
  const skills = selection.skills.slice(0, TOP_SKILLS);
  return (
    <Card>
      <CardTitle Icon={TrendingUp} aside={`${selection.label} · ${plural(selection.ads, "ad")}`}>
        Top skills demand
      </CardTitle>

      {skills.length > 0 ? (
        <ul className="space-y-4">
          {skills.map((skill) => (
            <SkillBar key={skill.skill} skill={skill} adsWithText={selection.adsWithText} />
          ))}
        </ul>
      ) : (
        <p className="text-sm font-medium text-ink/70">
          {selection.ads === 0
            ? `No ads collected for ${selection.sector?.sector ?? "this selection"} yet.`
            : "No skills could be read from these ads (their flyers have no readable requirements)."}
        </p>
      )}

      {selection.adsWithText > 0 && selection.adsWithText < SMALL_SAMPLE && (
        <p className="mt-5 rounded-xl border-2 border-ink/20 bg-[#fff6ea] px-3 py-2 text-xs font-medium text-ink/70">
          Based on {plural(selection.adsWithText, "ad")} with readable text, so the percentages are only
          indicative. They become reliable as more ads are collected.
        </p>
      )}
    </Card>
  );
}

function SkillBar({ skill, adsWithText }: { skill: SkillDemand; adsWithText: number }) {
  const percent = Math.round(skill.share * 100);
  return (
    <li className="flex items-center gap-3">
      <span title={skill.category}>
        <IconBox Icon={categoryIcons[skill.category] ?? BookOpen} className="bg-[#edddfc]" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-3">
          <span className="truncate text-sm font-bold text-ink">{skill.skill}</span>
          <span className="shrink-0 text-sm font-black text-[#4338ca]">{percent}%</span>
        </div>
        <div aria-hidden="true" className="mt-1.5 h-3 rounded-full border-2 border-ink bg-page">
          <div className="h-full rounded-full bg-lime" style={{ width: `${percent}%` }} />
        </div>
        <p className="mt-1 text-[11px] font-medium text-ink/60">
          {skill.ads} of {plural(adsWithText, "ad")} · {skill.category}
        </p>
      </div>
    </li>
  );
}

export function DataSourcesCard({ sources }: { sources: Source[] }) {
  return (
    <Card>
      <CardTitle Icon={Globe} aside="Sri Lankan job sites">
        Data sources
      </CardTitle>

      <ul className="divide-y-2 divide-ink overflow-hidden rounded-xl border-2 border-ink">
        {sources.map((source) => (
          <li key={source.site} className="flex items-center justify-between gap-3 bg-white px-4 py-3">
            <div className="min-w-0">
              <span className="flex items-center gap-2 text-sm font-bold">
                <span
                  aria-hidden="true"
                  className={`size-2.5 shrink-0 rounded-full border border-ink ${source.collected ? "bg-green-500" : "bg-red-500"}`}
                />
                <a href={source.url} target="_blank" rel="noreferrer" className="underline-offset-4 hover:underline">
                  {source.name}
                </a>
              </span>
              {!source.collected && (
                <span className="mt-0.5 block pl-[18px] text-xs text-ink/60" title={source.reason ?? undefined}>
                  Not allowed by the site&apos;s terms
                </span>
              )}
            </div>
            {source.collected ? (
              <span className="shrink-0 rounded-full border-2 border-ink bg-lime px-2.5 py-0.5 text-xs font-black">
                {plural(source.ads, "ad")}
              </span>
            ) : (
              <span className="shrink-0 text-xs font-semibold text-ink/60">Not collected</span>
            )}
          </li>
        ))}
      </ul>

      <p className="mt-4 flex gap-2 rounded-xl border-2 border-ink bg-peach p-3 text-xs font-medium leading-relaxed">
        <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        Each sync adds new ads and drops expired or removed ones from these numbers. Syncs are started by hand
        for now; automatic daily syncing is coming soon.
      </p>

      <ButtonLink href="/skills-profile" className="mt-5 w-full">
        Skills page
        <ChevronCircleIcon className="size-5" strokeWidth={1.75} />
      </ButtonLink>
    </Card>
  );
}

/** Needs ads collected over time, which the daily sync will provide. */
export function DeadSkillsCard() {
  return (
    <Card>
      <CardTitle Icon={TrendingDown}>Dead skills</CardTitle>
      <p className="flex gap-3 rounded-xl border-2 border-dashed border-ink/40 p-4 text-sm leading-relaxed text-ink/70">
        <TrendingDown className="mt-0.5 size-5 shrink-0" aria-hidden="true" />
        Skills that job ads ask for less and less over time. Shown once ads have been collected over several weeks.
      </p>
    </Card>
  );
}

export function Notice({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card className="mt-6 bg-cream">
      <h2 className="text-xl font-extrabold">{title}</h2>
      <div className="mt-2 text-sm leading-relaxed">{children}</div>
    </Card>
  );
}

function formatCounts(counts: Record<string, number>): string {
  return Object.entries(counts)
    .map(([label, count]) => `${label} (${count})`)
    .join(", ");
}

export function plural(count: number, word: string): string {
  return `${count.toLocaleString("en")} ${word}${count === 1 ? "" : "s"}`;
}
