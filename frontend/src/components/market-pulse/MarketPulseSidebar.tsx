import { Activity } from "lucide-react";
import Link from "next/link";

export const marketViews = {
  overview: "Overview",
  skills: "Skills demand",
  roles: "Job roles",
  industries: "Industries",
  sources: "Sources",
  sync: "Sync status",
  "dead-skills": "Dead skills",
} as const;

export type MarketView = keyof typeof marketViews;

export function parseView(value: string): MarketView {
  return value in marketViews ? (value as MarketView) : "overview";
}

export type Query = { role: string; sector: string };

/** The page address for a view, keeping the selected industry and role. */
export function viewHref(view: MarketView, { role, sector }: Query): string {
  const params = new URLSearchParams();
  if (view !== "overview") params.set("view", view);
  if (sector) params.set("sector", sector);
  if (role) params.set("role", role);
  const query = params.toString();
  return `/market-pulse${query ? `?${query}` : ""}`;
}

type SidebarProps = {
  view: MarketView;
  query: Query;
  counts: { skills: number; roles: number; industries: number; sourcesCollected: number; sources: number };
  syncedAgo: string | null;
  syncedOn: string | null;
  stale: boolean;
};

type Item = { view: MarketView; badge?: string };

/**
 * Market Pulse's own menu, below the site header: a full-height dark column on wide screens (it stays
 * in view while the page scrolls) and a dark bar of links on phones.
 */
export function MarketPulseSidebar({ view, query, counts, syncedAgo, syncedOn, stale }: SidebarProps) {
  const groups: { title: string; muted?: boolean; items: Item[] }[] = [
    {
      title: "Reports",
      items: [
        { view: "overview" },
        { view: "skills", badge: String(counts.skills) },
        { view: "roles", badge: String(counts.roles) },
        { view: "industries", badge: String(counts.industries) },
      ],
    },
    { title: "Data", items: [{ view: "sources", badge: `${counts.sourcesCollected} of ${counts.sources}` }, { view: "sync" }] },
    { title: "Coming soon", muted: true, items: [{ view: "dead-skills", badge: "Soon" }] },
  ];
  const freshness = syncedAgo ? `Last sync ${syncedAgo}` : "Not synced yet";

  return (
    <aside aria-label="Market Pulse" className="bg-[#17161d] text-[#d9d7e3] lg:w-[250px] lg:shrink-0">
      <div className="flex flex-col gap-4 px-3 py-4 lg:sticky lg:top-0 lg:h-[calc(100vh-4rem)] lg:gap-5 lg:overflow-y-auto lg:py-5">
        <div className="flex items-center gap-2.5 px-2">
          <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-[#d0ffa4] text-[#17161d]">
            <Activity className="size-[18px]" strokeWidth={2.2} aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <p className="text-[15px] font-bold text-white">Market Pulse</p>
            <p className="text-xs text-[#9a98a8]">Job market analytics</p>
          </div>
        </div>

        {/* Wide screens: grouped menu. */}
        <nav aria-label="Market Pulse views" className="hidden flex-col gap-4 lg:flex">
          {groups.map((group) => (
            <div key={group.title}>
              <p className="mb-1 px-2.5 text-[11px] font-semibold uppercase tracking-[0.1em] text-[#8c8a99]">{group.title}</p>
              <ul className="flex flex-col gap-0.5">
                {group.items.map((item) => (
                  <li key={item.view}>
                    <SidebarLink item={item} current={item.view === view} muted={group.muted} query={query} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        {/* Phones: one row of links that scrolls sideways. */}
        <nav aria-label="Market Pulse views" className="-mx-3 overflow-x-auto px-3 lg:hidden">
          <ul className="flex gap-1">
            {groups.flatMap((group) =>
              group.items.map((item) => (
                <li key={item.view} className="shrink-0">
                  <Link
                    href={viewHref(item.view, query)}
                    prefetch={false}
                    aria-current={item.view === view ? "page" : undefined}
                    className={`flex min-h-10 items-center whitespace-nowrap rounded-lg px-3 text-sm ${
                      item.view === view ? "bg-[#26242f] font-semibold text-[#d0ffa4]" : group.muted ? "text-[#8c8a99]" : "text-[#d9d7e3]"
                    }`}
                  >
                    {marketViews[item.view]}
                  </Link>
                </li>
              )),
            )}
          </ul>
        </nav>

        <div className="rounded-xl border border-[#2f2d3a] bg-[#23212c] px-3 py-2.5 lg:mt-auto lg:py-3">
          <p className="flex items-center gap-2 text-[13px] font-bold text-white">
            <span aria-hidden="true" className={`size-2 shrink-0 rounded-full ${stale ? "bg-[#f5b13d]" : "bg-[#7ee08a]"}`} />
            {freshness}
          </p>
          <p className="mt-1 text-xs text-[#a9a7b6]">
            {syncedOn ? `${syncedOn}. ` : ""}Ads are synced once a day.
          </p>
        </div>
      </div>
    </aside>
  );
}

function SidebarLink({ item, current, muted, query }: { item: Item; current: boolean; muted?: boolean; query: Query }) {
  return (
    <Link
      href={viewHref(item.view, query)}
      prefetch={false}
      aria-current={current ? "page" : undefined}
      className={`relative flex min-h-9 items-center gap-2.5 rounded-lg px-2.5 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[#d0ffa4] ${
        current ? "bg-[#26242f] font-semibold text-white" : muted ? "text-[#8c8a99] hover:bg-[#201f28]" : "text-[#d9d7e3] hover:bg-[#201f28]"
      }`}
    >
      {current && <span aria-hidden="true" className="absolute inset-y-2 left-0 w-[3px] rounded-full bg-[#d0ffa4]" />}
      <span className="flex-1">{marketViews[item.view]}</span>
      {item.badge && (
        <span
          className={`rounded-full px-2 text-[11.5px] font-semibold ${
            muted ? "bg-[#3a2f12] text-[#f5c55d]" : "bg-[#2b2935] text-[#c9c7d6]"
          }`}
        >
          {item.badge}
        </span>
      )}
    </Link>
  );
}
