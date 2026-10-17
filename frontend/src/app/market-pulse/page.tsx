import { Cpu, Database, Globe, RefreshCw } from "lucide-react";
import type { Metadata } from "next";

import { Footer } from "@/components/home/Footer";
import { Navbar } from "@/components/home/Navbar";
import { MarketPulseFilters } from "@/components/market-pulse/MarketPulseFilters";
import {
  DataSourcesCard,
  DeadSkillsCard,
  Notice,
  RoleCard,
  RoleSummary,
  StatCards,
  TopSkillsCard,
  plural,
  type Stat,
} from "@/components/market-pulse/MarketPulsePanels";
import { requireUser } from "@/lib/auth";
import { getMarketPulse, lastSync, selectView, timeAgo, type MarketPulse } from "@/lib/marketPulse";

export const metadata: Metadata = { title: "Market Pulse — Skillaro" };

const PATH = "/market-pulse";

export default async function MarketPulsePage({ searchParams }: PageProps<"/market-pulse">) {
  await requireUser(PATH);
  const { role, sector } = await searchParams;
  const result = await getMarketPulse();

  return (
    <>
      <Navbar currentPath={PATH} />
      <main className="mx-auto w-full max-w-[1100px] px-4 pt-12 sm:px-6">
        <h1 className="font-mono text-[32px] font-bold tracking-[-0.01em]">Market pulse</h1>
        <p className="mt-1 text-[16px] text-muted">Track the skills job ads ask for, by job role and industry</p>

        {result.status === "ok" && <Dashboard data={result.data} role={first(role)} sector={first(sector)} />}
        {result.status === "no-data" && (
          <Notice title="No market data yet">
            <p>Job ads have not been collected and profiled yet.</p>
            <p className="mt-2 text-[13px] text-muted">{result.message}</p>
          </Notice>
        )}
        {result.status === "unavailable" && (
          <Notice title="Market data can't be loaded right now">
            <p>The job market service isn&apos;t reachable. Please try again shortly.</p>
          </Notice>
        )}
      </main>
      <Footer />
    </>
  );
}

function Dashboard({ data, role, sector }: { data: MarketPulse; role: string; sector: string }) {
  const selection = selectView(data, role, sector);
  const synced = lastSync(data.sources);
  const collected = data.sources.filter((source) => source.collected);
  const stats: Stat[] = [
    { label: "Job ads collected", value: selection.ads.toLocaleString("en"), Icon: Database, tone: "bg-sun" },
    { label: "Unique skills extracted", value: selection.skills.length.toLocaleString("en"), Icon: Cpu, tone: "bg-pink" },
    {
      label: "Active data sources",
      value: String(collected.length),
      Icon: Globe,
      tone: "bg-cream",
      detail: collected.map((source) => source.name).join(", "),
    },
    { label: "Last sync", value: synced ? timeAgo(synced) : "–", Icon: RefreshCw, tone: "bg-white" },
  ];

  return (
    <>
      <section aria-label="Filters" className="mt-10 flex flex-col gap-10 sm:flex-row sm:items-start sm:gap-14">
        <RoleCard label={selection.label} />
        <div className="w-full max-w-[520px]">
          <MarketPulseFilters
            // A new selection (also via the browser's back button) resets the dropdowns to the URL.
            key={`${selection.role?.role ?? ""}|${selection.sector?.sector ?? ""}`}
            roles={data.roles.map(({ role, sectors, ads }) => ({ role, sectors, ads }))}
            sectors={data.sectors.map((s) => s.sector)}
            role={selection.role?.role ?? ""}
            sector={selection.sector?.sector ?? ""}
          />
          {selection.role ? (
            <RoleSummary role={selection.role} />
          ) : (
            <p className="mt-4 text-[13px] text-muted">
              {plural(data.totals.roles, "job role")} found in {plural(data.totals.ads, "ad")}. Pick one to see the
              skills its ads ask for.
            </p>
          )}
        </div>
      </section>

      <hr className="my-12 border-t-[3px] border-ink/15" />

      <section aria-label="Overview">
        <StatCards stats={stats} />
      </section>

      <div className="mt-12 grid gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="lg:self-start">
          <DataSourcesCard sources={data.sources} />
        </div>
        <div className="grid content-start gap-8">
          <TopSkillsCard selection={selection} />
          <DeadSkillsCard />
        </div>
      </div>
    </>
  );
}

function first(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? "";
}
