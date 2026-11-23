import type { ReactNode } from "react";

// Building blocks for Market Pulse: white cards with a hairline border on a light grey page, beside
// a near-black sidebar with lime highlights. Class names are written out in full so Tailwind finds them.

export const SMALL_SAMPLE = 10; // fewer ads with text than this: percentages are only indicative
const STALE_AFTER_MS = 2 * 24 * 60 * 60 * 1000; // the sync runs daily: older data is flagged

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-xl border border-[#e6e5ee] bg-white ${className}`}>{children}</section>;
}

/** A card's title row, with a short note or link on the right. */
export function CardHeader({ title, aside }: { title: ReactNode; aside?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 border-b border-[#eeedf3] px-4 py-3">
      <h2 className="text-[15px] font-bold text-[#17161d]">{title}</h2>
      {aside && <div className="text-xs text-[#6b6979]">{aside}</div>}
    </div>
  );
}

export type KpiProps = { label: string; value: string; detail?: string };

export function Kpi({ label, value, detail }: KpiProps) {
  return (
    <div className="min-w-0 rounded-xl border border-[#e6e5ee] bg-white px-4 py-3.5">
      <p className="text-[13px] text-[#5d5b6b]">{label}</p>
      <p className="mt-0.5 truncate text-2xl font-bold leading-tight text-[#17161d]" title={value}>
        {value}
      </p>
      {detail && (
        <p className="mt-0.5 truncate text-xs text-[#6b6979]" title={detail}>
          {detail}
        </p>
      )}
    </div>
  );
}

export function KpiRow({ items }: { items: KpiProps[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      {items.map((item) => (
        <Kpi key={item.label} {...item} />
      ))}
    </div>
  );
}

/** Each skill category's bar colour and tag colours (dark text on a light tint, readable on white). */
const categoryStyles: Record<string, { bar: string; tag: string }> = {
  "Soft skill": { bar: "bg-[#c58af0]", tag: "bg-[#f3e8fd] text-[#6b2fa0]" },
  "Domain knowledge": { bar: "bg-[#ffb36b]", tag: "bg-[#fff0e0] text-[#8a4b00]" },
  Technical: { bar: "bg-[#4a7fd0]", tag: "bg-[#e4edfb] text-[#1e4a8a]" },
  Qualification: { bar: "bg-[#47a77a]", tag: "bg-[#e3f4ea] text-[#1f6142]" },
  Tool: { bar: "bg-[#2ba6a0]", tag: "bg-[#ddf4f2] text-[#0b6670]" },
  Language: { bar: "bg-[#e0c23b]", tag: "bg-[#fbf3d5] text-[#7a5d00]" },
};
const otherCategory = { bar: "bg-[#9a98a8]", tag: "bg-[#f1f0f5] text-[#4a4858]" };

export function categoryStyle(category: string) {
  return categoryStyles[category] ?? otherCategory;
}

export function CategoryTag({ category }: { category: string }) {
  return (
    <span className={`inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold ${categoryStyle(category).tag}`}>
      {category}
    </span>
  );
}

/** Colours for industries, by their order (most ads first). */
const industryColors = ["bg-[#4a7fd0]", "bg-[#c58af0]", "bg-[#ffb36b]", "bg-[#47a77a]", "bg-[#2ba6a0]", "bg-[#e0c23b]"];

export function industryColor(index: number): string {
  return industryColors[index % industryColors.length];
}

export function SmallSampleNote({ adsWithText }: { adsWithText: number }) {
  if (adsWithText === 0 || adsWithText >= SMALL_SAMPLE) return null;
  return (
    <p className="rounded-lg border border-[#f3dfb0] bg-[#fdf6e3] px-3.5 py-2.5 text-[13px] text-[#6b4a00]">
      Based on {plural(adsWithText, "ad")} with readable text, so these percentages are only a guide. They firm up as
      more ads are collected.
    </p>
  );
}

export function plural(count: number, word: string): string {
  return `${count.toLocaleString("en")} ${word}${count === 1 ? "" : "s"}`;
}

/** "a", "a and b", "a, b and c". */
export function listJoin(items: string[]): string {
  return items.length <= 1 ? (items[0] ?? "") : `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

export function percent(share: number): number {
  return Math.round(share * 100);
}

/** Dates and times in Sri Lanka time, where the ads are collected. */
export function formatDate(iso: string, withTime = false): string {
  return new Date(iso).toLocaleString("en-GB", {
    timeZone: "Asia/Colombo",
    day: "numeric",
    month: "short",
    year: "numeric",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  });
}

/** Whether the newest data is older than the daily sync should allow. */
export function isStale(synced: string | null): boolean {
  return !synced || Date.now() - Date.parse(synced) > STALE_AFTER_MS;
}
