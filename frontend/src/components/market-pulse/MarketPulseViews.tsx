import { ArrowLeft, CircleSlash, ExternalLink, TrendingDown, type LucideIcon } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import type { MarketPulse, RoleProfile, SectorProfile, Selection, SkillDemand, Source } from "@/lib/marketPulse";

import { viewHref, type Query } from "./MarketPulseSidebar";
import {
  Card,
  CardHeader,
  CategoryTag,
  categoryStyle,
  formatDate,
  industryColor,
  KpiRow,
  listJoin,
  percent,
  plural,
  SmallSampleNote,
} from "./ui";

const linkClass = "font-semibold text-[#4338ca] underline-offset-4 hover:underline";
const VISIBLE_TITLES = 12; // more job titles than this fold away behind "Show more"

// ---------------------------------------------------------------- Overview

export function OverviewView({ data, selection, query }: { data: MarketPulse; selection: Selection; query: Query }) {
  const top = selection.skills[0];
  const knownRoles = data.totals.roles - data.totals.unmapped_roles;
  const sectorRoles = data.roles.filter((r) => r.sectors.includes(query.sector)).length;
  return (
    <>
      <KpiRow
        items={[
          { label: "Job ads", value: selection.ads.toLocaleString("en"), detail: `${selection.adsWithText.toLocaleString("en")} with readable text` },
          { label: "Unique skills", value: selection.skills.length.toLocaleString("en"), detail: selection.label },
          selection.role
            ? { label: "Most asked skill", value: top ? `${percent(top.share)}%` : "–", detail: top?.skill ?? "No skills read yet" }
            : query.sector
              ? { label: "Job roles", value: String(sectorRoles), detail: `in ${query.sector}` }
              : { label: "Job roles", value: String(data.totals.roles), detail: `${knownRoles} known roles + ${data.totals.unmapped_roles} other titles` },
          { label: "Industries", value: String(data.sectors.length), detail: listJoin(sortedSectors(data.sectors).map((s) => s.sector)) },
        ]}
      />
      {selection.role && (
        <p className="rounded-lg border border-[#e6e5ee] bg-white px-4 py-3 text-sm">
          Showing <strong>{selection.role.role}</strong>.{" "}
          <Link href={viewHref("roles", query)} prefetch={false} className={linkClass}>
            See its experience, seniority and job titles
          </Link>
        </p>
      )}
      <SmallSampleNote adsWithText={selection.adsWithText} />
      <SkillMixCard skills={selection.skills} />
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <TopSkillsCard selection={selection} query={query} />
        <IndustriesCompared sectors={data.sectors} />
      </div>
    </>
  );
}

function TopSkillsCard({ selection, query }: { selection: Selection; query: Query }) {
  const skills = selection.skills.slice(0, 8);
  return (
    <Card className="min-w-0">
      <CardHeader
        title="Top skills"
        aside={
          selection.skills.length > 0 && (
            <Link href={viewHref("skills", query)} prefetch={false} className={linkClass}>
              All {selection.skills.length}
            </Link>
          )
        }
      />
      {skills.length > 0 ? (
        <ol className="py-1">
          {skills.map((skill, index) => (
            <li key={skill.skill} className="flex items-center gap-3 px-4 py-2 text-sm">
              <span className="w-5 shrink-0 text-[#6b6979] tabular-nums">{index + 1}</span>
              <span className="min-w-0 flex-1 truncate font-semibold" title={skill.skill}>
                {skill.skill}
              </span>
              <ShareBar share={skill.share} className="w-20 sm:w-28" />
            </li>
          ))}
        </ol>
      ) : (
        <NoSkills selection={selection} />
      )}
    </Card>
  );
}

// ---------------------------------------------------------------- Skills demand

export function SkillsView({ selection }: { selection: Selection }) {
  return (
    <>
      <SmallSampleNote adsWithText={selection.adsWithText} />
      <SkillMixCard skills={selection.skills} />
      <Card className="min-w-0">
        <CardHeader title="All skills" aside={`Share of ${plural(selection.adsWithText, "ad")} with readable text`} />
        {selection.skills.length > 0 ? (
          <SkillsTable skills={selection.skills} />
        ) : (
          <NoSkills selection={selection} />
        )}
      </Card>
    </>
  );
}

function SkillsTable({ skills }: { skills: SkillDemand[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[34rem] text-sm">
        <thead>
          <tr className="text-left text-[11.5px] uppercase tracking-wide text-[#6b6979]">
            <th className="w-10 px-4 py-2 font-semibold">#</th>
            <th className="px-2 py-2 font-semibold">Skill</th>
            <th className="px-2 py-2 font-semibold">Category</th>
            <th className="px-2 py-2 text-right font-semibold">Ads</th>
            <th className="w-[32%] px-4 py-2 font-semibold">Share</th>
          </tr>
        </thead>
        <tbody>
          {skills.map((skill, index) => (
            <tr key={skill.skill} className="border-t border-[#f1f0f5]">
              <td className="px-4 py-2 text-[#6b6979] tabular-nums">{index + 1}</td>
              <td className="px-2 py-2 font-semibold">{skill.skill}</td>
              <td className="px-2 py-2">
                <CategoryTag category={skill.category} />
              </td>
              <td className="px-2 py-2 text-right tabular-nums text-[#5d5b6b]">{skill.ads}</td>
              <td className="px-4 py-2">
                <ShareBar share={skill.share} className="flex-1" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** The share of every skill mention that falls in each category, as one stacked bar. */
function SkillMixCard({ skills }: { skills: SkillDemand[] }) {
  const totals = new Map<string, number>();
  for (const skill of skills) totals.set(skill.category, (totals.get(skill.category) ?? 0) + skill.ads);
  const sum = [...totals.values()].reduce((a, b) => a + b, 0);
  if (sum === 0) return null;
  const mix = [...totals].map(([category, ads]) => ({ category, share: ads / sum })).sort((a, b) => b.share - a.share);
  return (
    <Card>
      <CardHeader title="Skill mix" aside="Every skill mention in the ads, by category" />
      <div className="px-4 py-3.5">
        <div
          role="img"
          aria-label={mix.map((m) => `${m.category} ${percent(m.share)}%`).join(", ")}
          className="flex h-5 overflow-hidden rounded-md"
        >
          {mix.map((m) => (
            <div key={m.category} className={categoryStyle(m.category).bar} style={{ width: `${m.share * 100}%` }} />
          ))}
        </div>
        <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-[13px]">
          {mix.map((m) => (
            <li key={m.category} className="flex items-center gap-1.5">
              <span aria-hidden="true" className={`size-2.5 rounded-sm ${categoryStyle(m.category).bar}`} />
              {m.category} <strong className="tabular-nums">{percent(m.share)}%</strong>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------- Job roles

export function RolesView({ data, selection, query }: { data: MarketPulse; selection: Selection; query: Query }) {
  if (selection.role) return <RoleDetail role={selection.role} query={query} />;

  const inSector = query.sector ? data.roles.filter((r) => r.sectors.includes(query.sector)) : data.roles;
  const byAds = (a: RoleProfile, b: RoleProfile) => b.ads - a.ads || a.role.localeCompare(b.role);
  const known = inSector.filter((r) => r.mapped).sort(byAds);
  const other = inSector.filter((r) => !r.mapped).sort(byAds);
  return (
    <Card className="min-w-0">
      <CardHeader
        title={query.sector ? `Job roles in ${query.sector}` : "Job roles"}
        aside={`${plural(known.length, "role")}, most ads first`}
      />
      <RolesTable roles={known} query={query} />
      {other.length > 0 && (
        <details className="group border-t border-[#eeedf3]">
          <summary className="flex min-h-11 cursor-pointer list-none items-center px-4 text-sm font-semibold text-[#4338ca] [&::-webkit-details-marker]:hidden">
            <span className="group-open:hidden">Show {plural(other.length, "other job title")}</span>
            <span className="hidden group-open:inline">Hide the other job titles</span>
          </summary>
          <p className="px-4 pb-2 text-xs text-[#6b6979]">One-off job titles that could not be matched to a known role.</p>
          <RolesTable roles={other} query={query} />
        </details>
      )}
    </Card>
  );
}

function RolesTable({ roles, query }: { roles: RoleProfile[]; query: Query }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[38rem] text-sm">
        <thead>
          <tr className="text-left text-[11.5px] uppercase tracking-wide text-[#6b6979]">
            <th className="px-4 py-2 font-semibold">Job role</th>
            <th className="px-2 py-2 font-semibold">Industries</th>
            <th className="px-2 py-2 text-right font-semibold">Ads</th>
            <th className="px-4 py-2 font-semibold">Most asked skill</th>
          </tr>
        </thead>
        <tbody>
          {roles.map((role) => {
            const top = role.skills[0];
            return (
              <tr key={role.role} className="border-t border-[#f1f0f5]">
                <td className="px-4 py-2.5">
                  <Link href={viewHref("roles", { sector: query.sector, role: role.role })} prefetch={false} className={linkClass}>
                    {role.role}
                  </Link>
                </td>
                <td className="px-2 py-2.5 text-[#5d5b6b]">{role.sectors.join(", ")}</td>
                <td className="px-2 py-2.5 text-right tabular-nums">{role.ads}</td>
                <td className="px-4 py-2.5">
                  {top ? (
                    <>
                      {top.skill} <span className="font-bold text-[#4338ca] tabular-nums">{percent(top.share)}%</span>
                    </>
                  ) : (
                    <span className="text-[#6b6979]">No skills read</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RoleDetail({ role, query }: { role: RoleProfile; query: Query }) {
  const top = role.skills[0];
  const experience = mostCommon(role.experience);
  const seniority = mostCommon(role.seniority);
  return (
    <>
      <Link
        href={viewHref("roles", { sector: query.sector, role: "" })}
        prefetch={false}
        className="inline-flex items-center gap-1.5 self-start text-sm font-semibold text-[#4338ca] underline-offset-4 hover:underline"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        All job roles
      </Link>
      <KpiRow
        items={[
          { label: "Job ads", value: String(role.ads), detail: `${role.ads_with_text} with readable text` },
          { label: "Most asked skill", value: top ? `${percent(top.share)}%` : "–", detail: top?.skill ?? "No skills read yet" },
          { label: "Seniority", value: seniority?.label ?? "–", detail: seniority ? `in ${seniority.count} of ${plural(role.ads, "ad")}` : undefined },
          { label: "Experience asked", value: experience?.label ?? "–", detail: experience ? `in ${experience.count} of ${plural(role.ads, "ad")}` : undefined },
        ]}
      />
      <SmallSampleNote adsWithText={role.ads_with_text} />
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <Card className="min-w-0">
          <CardHeader
            title="Skills these ads ask for"
            aside={
              role.skills.length > 10 && (
                <Link href={viewHref("skills", query)} prefetch={false} className={linkClass}>
                  All {role.skills.length}
                </Link>
              )
            }
          />
          {role.skills.length > 0 ? (
            <SkillsTable skills={role.skills.slice(0, 10)} />
          ) : (
            <p className="px-4 py-6 text-sm text-[#5d5b6b]">No skills could be read from these ads.</p>
          )}
        </Card>
        <div className="flex min-w-0 flex-col gap-4">
          <CountsCard title="Seniority" counts={role.seniority} />
          <CountsCard title="Experience asked" counts={role.experience} />
          <TitlesCard titles={role.titles} />
        </div>
      </div>
    </>
  );
}

function CountsCard({ title, counts }: { title: string; counts: Record<string, number> }) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return (
    <Card>
      <CardHeader title={title} />
      {entries.length > 0 ? (
        <ul className="flex flex-wrap gap-1.5 px-4 py-3">
          {entries.map(([label, count]) => (
            <li key={label} className="rounded-full bg-[#f1f0f5] px-2.5 py-1 text-[13px]">
              {label} <strong className="tabular-nums">{count}</strong>
            </li>
          ))}
        </ul>
      ) : (
        <p className="px-4 py-3 text-sm text-[#5d5b6b]">Not given in these ads.</p>
      )}
    </Card>
  );
}

function TitlesCard({ titles }: { titles: string[] }) {
  const shown = titles.slice(0, VISIBLE_TITLES);
  const rest = titles.slice(VISIBLE_TITLES);
  return (
    <Card>
      <CardHeader title="Job titles in these ads" aside={plural(titles.length, "title")} />
      <div className="px-4 py-3">
        <TitleChips titles={shown} />
        {rest.length > 0 && (
          <details className="group mt-1">
            <summary className="flex min-h-10 cursor-pointer list-none items-center text-sm font-semibold text-[#4338ca] [&::-webkit-details-marker]:hidden">
              <span className="group-open:hidden">Show {rest.length} more</span>
              <span className="hidden group-open:inline">Show fewer</span>
            </summary>
            <TitleChips titles={rest} />
          </details>
        )}
      </div>
    </Card>
  );
}

function TitleChips({ titles }: { titles: string[] }) {
  return (
    <ul className="flex flex-wrap gap-1.5">
      {titles.map((title) => (
        <li key={title} className="rounded-md border border-[#e6e5ee] px-2 py-1 text-[13px]">
          {title}
        </li>
      ))}
    </ul>
  );
}

// ---------------------------------------------------------------- Industries

export function IndustriesView({ data }: { data: MarketPulse }) {
  return (
    <>
      <IndustriesCompared sectors={data.sectors} />
      <SkillsHeatmap sectors={data.sectors} />
    </>
  );
}

/** Each industry's ad count and the skill its ads ask for most, with a one-line summary. */
function IndustriesCompared({ sectors }: { sectors: SectorProfile[] }) {
  const ordered = sortedSectors(sectors);
  const leaders = new Map<string, string[]>();
  for (const sector of ordered) {
    const top = sector.skills[0];
    if (top) leaders.set(top.skill, [...(leaders.get(top.skill) ?? []), sector.sector]);
  }
  const summary = [...leaders].map(([skill, names]) => `${skill} in ${listJoin(names)}`).join("; ");
  return (
    <Card className="min-w-0">
      <CardHeader title="Industries compared" aside="Most asked skill in each" />
      <div className="overflow-x-auto">
        <table className="w-full min-w-[24rem] text-sm">
          <thead>
            <tr className="text-left text-[11.5px] uppercase tracking-wide text-[#6b6979]">
              <th className="px-4 py-2 font-semibold">Industry</th>
              <th className="px-2 py-2 text-right font-semibold">Ads</th>
              <th className="px-2 py-2 font-semibold">Most asked skill</th>
              <th className="px-4 py-2 text-right font-semibold">Share</th>
            </tr>
          </thead>
          <tbody>
            {ordered.map((sector, index) => {
              const top = sector.skills[0];
              return (
                <tr key={sector.sector} className="border-t border-[#f1f0f5]">
                  <th scope="row" className="px-4 py-2.5 text-left font-semibold">
                    <Link
                      href={viewHref("overview", { sector: sector.sector, role: "" })}
                      prefetch={false}
                      className="inline-flex items-center gap-2 underline-offset-4 hover:underline"
                    >
                      <span aria-hidden="true" className={`size-2 rounded-sm ${industryColor(index)}`} />
                      {sector.sector}
                    </Link>
                  </th>
                  <td className="px-2 py-2.5 text-right tabular-nums">{sector.ads}</td>
                  <td className="px-2 py-2.5">{top?.skill ?? "–"}</td>
                  <td className="px-4 py-2.5 text-right font-bold text-[#4338ca] tabular-nums">{top ? `${percent(top.share)}%` : "–"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {summary && <p className="border-t border-[#eeedf3] px-4 py-2.5 text-xs text-[#5d5b6b]">Most asked: {summary}.</p>}
    </Card>
  );
}

/** The top skills of every industry, with each one's share in every industry. */
function SkillsHeatmap({ sectors }: { sectors: SectorProfile[] }) {
  const ordered = sortedSectors(sectors);
  const names: string[] = [];
  for (const sector of ordered) {
    for (const skill of sector.skills.slice(0, 3)) if (!names.includes(skill.skill)) names.push(skill.skill);
  }
  if (names.length === 0) return null;
  return (
    <Card className="min-w-0">
      <CardHeader title="Skills across industries" aside="Share of each industry's readable ads asking for a skill" />
      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] text-sm">
          <thead>
            <tr>
              <th className="px-4 py-2.5 text-left text-[11.5px] font-semibold uppercase tracking-wide text-[#6b6979]">Skill</th>
              {ordered.map((sector, index) => (
                <th key={sector.sector} className="px-2 py-2.5 text-center">
                  <span className="inline-flex items-center gap-1.5 font-semibold">
                    <span aria-hidden="true" className={`size-2 rounded-sm ${industryColor(index)}`} />
                    {sector.sector}
                  </span>
                  <span className="block text-xs font-normal text-[#6b6979]">{sector.ads_with_text} readable ads</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {names.map((name) => (
              <tr key={name} className="border-t border-[#f1f0f5]">
                <th scope="row" className="px-4 py-1.5 text-left font-semibold">
                  {name}
                </th>
                {ordered.map((sector) => {
                  const share = percent(sector.skills.find((s) => s.skill === name)?.share ?? 0);
                  return (
                    <td key={sector.sector} className="px-1.5 py-1">
                      <span className={`block rounded-md py-2 text-center tabular-nums ${heatClass(share)}`}>{share ? `${share}%` : "–"}</span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-[#eeedf3] px-4 py-2.5 text-xs text-[#5d5b6b]">
        {[
          [0, "none"],
          [10, "under 20%"],
          [30, "20–39%"],
          [50, "40–59%"],
          [70, "60% or more"],
        ].map(([sample, label]) => (
          <li key={label} className="flex items-center gap-1.5">
            <span aria-hidden="true" className={`h-3 w-5 rounded-sm ${heatClass(Number(sample))}`} />
            {label}
          </li>
        ))}
      </ul>
    </Card>
  );
}

function heatClass(share: number): string {
  if (share === 0) return "bg-[#faf9fb] text-[#6b6979]";
  if (share < 20) return "bg-[#f3ecfd]";
  if (share < 40) return "bg-[#e3d2fb]";
  if (share < 60) return "bg-[#cdb2f7] font-bold";
  return "bg-[#b48ef1] font-bold";
}

// ---------------------------------------------------------------- Sources and sync

export function SourcesView({ sources }: { sources: Source[] }) {
  const collected = sources.filter((s) => s.collected).length;
  return (
    <Card>
      <CardHeader title="Sri Lankan job sites" aside={`${collected} of ${sources.length} collected`} />
      <ul className="divide-y divide-[#f1f0f5]">
        {sources.map((source) => (
          <li key={source.site} className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 px-4 py-3">
            <div className="min-w-0">
              <a
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 font-semibold underline-offset-4 hover:underline"
              >
                {source.name}
                <ExternalLink className="size-3.5 text-[#6b6979]" aria-hidden="true" />
              </a>
              <p className="text-xs text-[#6b6979]" title={source.reason ?? undefined}>
                {source.collected
                  ? source.last_collected
                    ? `Last collected ${formatDate(source.last_collected, true)}`
                    : "Not collected yet"
                  : "The site's terms don't allow collecting its ads"}
              </p>
            </div>
            {source.collected ? (
              <span className="rounded-full bg-[#e3f4ea] px-2.5 py-0.5 text-xs font-semibold text-[#1f6142]">{plural(source.ads, "ad")}</span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-[#f1f0f5] px-2.5 py-0.5 text-xs font-semibold text-[#4a4858]">
                <CircleSlash className="size-3.5" aria-hidden="true" />
                Not collected
              </span>
            )}
          </li>
        ))}
      </ul>
      <p className="border-t border-[#eeedf3] px-4 py-3 text-xs text-[#5d5b6b]">
        Only sites whose terms allow it are collected. Personal details in the ads are removed before they are stored.
      </p>
    </Card>
  );
}

export function SyncView({ sources, synced, syncedAgo, stale }: { sources: Source[]; synced: string | null; syncedAgo: string | null; stale: boolean }) {
  return (
    <>
      <Card className="px-4 py-4">
        <p className="flex items-center gap-2 text-lg font-bold">
          <span aria-hidden="true" className={`size-2.5 rounded-full ${stale ? "bg-[#f5b13d]" : "bg-[#3fbf63]"}`} />
          {syncedAgo ? `Last sync ${syncedAgo}` : "Not synced yet"}
        </p>
        {synced && <p className="mt-0.5 text-sm text-[#5d5b6b]">{formatDate(synced, true)} (Sri Lanka time)</p>}
        <p className="mt-3 text-sm">
          {stale
            ? "The data is more than two days old. Newer ads will show after the next sync."
            : "The data is up to date."}{" "}
          Ads are synced once a day: each sync adds new ads and drops expired or removed ones.
        </p>
      </Card>
      <Card className="min-w-0">
        <CardHeader title="Each site" />
        <div className="overflow-x-auto">
          <table className="w-full min-w-[34rem] text-sm">
            <thead>
              <tr className="text-left text-[11.5px] uppercase tracking-wide text-[#6b6979]">
                <th className="px-4 py-2 font-semibold">Site</th>
                <th className="px-2 py-2 font-semibold">Last checked</th>
                <th className="px-2 py-2 font-semibold">Last collected</th>
                <th className="px-4 py-2 text-right font-semibold">Ads</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source) => (
                <tr key={source.site} className="border-t border-[#f1f0f5]">
                  <th scope="row" className="px-4 py-2.5 text-left font-semibold">
                    {source.name}
                  </th>
                  <td className="px-2 py-2.5 text-[#5d5b6b]">
                    {source.collected ? (source.last_checked ? formatDate(source.last_checked, true) : "–") : "Not collected"}
                  </td>
                  <td className="px-2 py-2.5 text-[#5d5b6b]">
                    {source.collected && source.last_collected ? formatDate(source.last_collected, true) : "–"}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{source.collected ? source.ads : "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}

// ---------------------------------------------------------------- Dead skills and notices

export function DeadSkillsView() {
  return (
    <Notice Icon={TrendingDown} title="Dead skills are coming soon">
      Skills that job ads ask for less and less over time. They show here once ads have been collected over several
      weeks.
    </Notice>
  );
}

export function Notice({ Icon, title, children }: { Icon: LucideIcon; title: string; children: ReactNode }) {
  return (
    <Card className="flex flex-col items-center px-6 py-14 text-center">
      <span className="grid size-12 place-items-center rounded-full bg-[#f1f0f5] text-[#17161d]">
        <Icon className="size-6" aria-hidden="true" />
      </span>
      <h2 className="mt-4 text-lg font-bold">{title}</h2>
      <div className="mt-1 max-w-md text-sm text-[#5d5b6b]">{children}</div>
    </Card>
  );
}

// ---------------------------------------------------------------- Shared pieces

function ShareBar({ share, className = "" }: { share: number; className?: string }) {
  return (
    <span className={`flex items-center gap-2.5 ${className}`}>
      <span aria-hidden="true" className="h-1.5 min-w-10 flex-1 overflow-hidden rounded-full bg-[#efeef4]">
        <span className="block h-full rounded-full bg-[#17161d]" style={{ width: `${share * 100}%` }} />
      </span>
      <span className="w-10 shrink-0 text-right font-bold tabular-nums">{percent(share)}%</span>
    </span>
  );
}

function NoSkills({ selection }: { selection: Selection }) {
  return (
    <p className="px-4 py-8 text-center text-sm text-[#5d5b6b]">
      {selection.ads === 0
        ? "No ads collected for this selection yet."
        : "No skills could be read from these ads (their flyers have no readable requirements)."}
    </p>
  );
}

function sortedSectors(sectors: SectorProfile[]): SectorProfile[] {
  return [...sectors].sort((a, b) => b.ads - a.ads || a.sector.localeCompare(b.sector));
}

/** The most common value (e.g. seniority) and how many ads give it. */
function mostCommon(counts: Record<string, number>): { label: string; count: number } | null {
  const [entry] = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return entry ? { label: entry[0], count: entry[1] } : null;
}
