import { CloudOff, Database } from "lucide-react";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Footer } from "@/components/home/Footer";
import { Navbar } from "@/components/home/Navbar";
import { MarketPulseFilters } from "@/components/market-pulse/MarketPulseFilters";
import { MarketPulseSidebar, marketViews, parseView, type MarketView, type Query } from "@/components/market-pulse/MarketPulseSidebar";
import {
  DeadSkillsView,
  IndustriesView,
  Notice,
  OverviewView,
  RolesView,
  SkillsView,
  SourcesView,
  SyncView,
} from "@/components/market-pulse/MarketPulseViews";
import { formatDate, isStale, plural } from "@/components/market-pulse/ui";
import { requireUser } from "@/lib/auth";
import { getMarketPulse, lastSync, selectView, timeAgo, type MarketPulse } from "@/lib/marketPulse";

export const metadata: Metadata = { title: "Market Pulse — Skillaro" };

const PATH = "/market-pulse";

// The views whose numbers follow the industry and role filters.
const FILTERED_VIEWS: MarketView[] = ["overview", "skills", "roles"];

export default async function MarketPulsePage({ searchParams }: PageProps<"/market-pulse">) {
  await requireUser(PATH);
  const params = await searchParams;
  const result = await getMarketPulse();

  return (
    <div
      className={`min-h-screen bg-[#f7f7f9] text-[#17161d] ${
        // On wide screens a dark strip under the sidebar runs it down to the footer.
        result.status === "ok" ? "lg:bg-[linear-gradient(to_right,#17161d_250px,#f7f7f9_250px)]" : ""
      }`}
    >
      <Navbar currentPath={PATH} />

      {result.status === "ok" ? (
        <MarketPulseLayout
          data={result.data}
          view={parseView(first(params.view))}
          role={first(params.role)}
          sector={first(params.sector)}
        />
      ) : (
        <main className="mx-auto max-w-3xl px-4 py-10">
          {result.status === "no-data" ? (
            <Notice Icon={Database} title="No market data yet">
              <p>Job ads have not been collected and profiled yet.</p>
              <p className="mt-2">{result.message}</p>
            </Notice>
          ) : (
            <Notice Icon={CloudOff} title="Market data can't be loaded right now">
              The job market service isn&apos;t reachable. Please try again shortly.
            </Notice>
          )}
        </main>
      )}

      <Footer />
    </div>
  );
}

/** The dark Market Pulse sidebar beside the chosen view. */
function MarketPulseLayout({ data, view, role, sector }: { data: MarketPulse; view: MarketView; role: string; sector: string }) {
  const selection = selectView(data, role, sector);
  // Only a role or industry that exists is kept, so links never carry an unknown one along.
  const query: Query = { role: selection.role?.role ?? "", sector: selection.sector?.sector ?? "" };
  const synced = lastSync(data.sources);
  const stale = isStale(synced);
  const syncedAgo = synced ? timeAgo(synced) : null;
  const collected = data.sources.filter((s) => s.collected);

  const header = {
    overview: { title: "Overview", subtitle: `${selection.label} · ${plural(selection.ads, "ad")}${synced ? ` · data as of ${formatDate(synced)}` : ""}` },
    skills: { title: "Skills demand", subtitle: `${selection.label} · every skill the ads ask for, most asked first` },
    roles: selection.role
      ? { title: selection.role.role, subtitle: `${selection.role.sectors.join(" · ")} · ${plural(selection.role.ads, "job ad")}` }
      : { title: "Job roles", subtitle: "The job roles found in the ads, and what each one asks for" },
    industries: { title: "Industries", subtitle: "What each industry's ads ask for" },
    sources: { title: "Sources", subtitle: "Where the job ads come from" },
    sync: { title: "Sync status", subtitle: "How fresh the data is" },
    "dead-skills": { title: "Dead skills", subtitle: "Skills job ads ask for less and less over time" },
  }[view];

  let content: ReactNode;
  switch (view) {
    case "skills":
      content = <SkillsView selection={selection} />;
      break;
    case "roles":
      content = <RolesView data={data} selection={selection} query={query} />;
      break;
    case "industries":
      content = <IndustriesView data={data} />;
      break;
    case "sources":
      content = <SourcesView sources={data.sources} />;
      break;
    case "sync":
      content = <SyncView sources={data.sources} synced={synced} syncedAgo={syncedAgo} stale={stale} />;
      break;
    case "dead-skills":
      content = <DeadSkillsView />;
      break;
    default:
      content = <OverviewView data={data} selection={selection} query={query} />;
  }

  return (
    <div className="lg:flex">
      <MarketPulseSidebar
        view={view}
        query={query}
        counts={{
          skills: data.totals.unique_skills,
          roles: data.totals.roles,
          industries: data.sectors.length,
          sourcesCollected: collected.length,
          sources: data.sources.length,
        }}
        syncedAgo={syncedAgo}
        syncedOn={synced ? formatDate(synced) : null}
        stale={stale}
      />

      <main className="min-w-0 flex-1 px-4 py-5 sm:px-6 lg:px-8 lg:py-6">
        <div className="mx-auto flex max-w-[1200px] flex-col gap-4">
          <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-[#6b6979]">
                Market Pulse{view !== "overview" && ` / ${marketViews[view]}`}
              </p>
              <h1 className="mt-0.5 text-2xl font-bold tracking-tight">{header.title}</h1>
              <p className="mt-0.5 text-sm text-[#5d5b6b]">{header.subtitle}</p>
            </div>
            {FILTERED_VIEWS.includes(view) && (
              <MarketPulseFilters
                // A new selection (also via the browser's back button) resets the dropdowns to the URL.
                key={`${query.role}|${query.sector}`}
                roles={[...data.roles]
                  .sort((a, b) => b.ads - a.ads || a.role.localeCompare(b.role))
                  .map(({ role, sectors, ads }) => ({ role, sectors, ads }))}
                sectors={data.sectors.map((s) => s.sector)}
                role={query.role}
                sector={query.sector}
                view={view}
              />
            )}
          </div>
          {content}
        </div>
      </main>
    </div>
  );
}

function first(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? "";
}
