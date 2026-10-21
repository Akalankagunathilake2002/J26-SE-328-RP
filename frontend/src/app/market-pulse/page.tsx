import { BarChart3, Cpu, Database, Globe, RefreshCw, SlidersHorizontal } from "lucide-react";
import type { Metadata } from "next";

import { Footer } from "@/components/home/Footer";
import { Navbar } from "@/components/home/Navbar";
import { MarketPulseFilters } from "@/components/market-pulse/MarketPulseFilters";
import {
  DataSourcesCard,
  DeadSkillsCard,
  MarketPulseHero,
  Notice,
  SelectionPanel,
  TopSkillsCard,
} from "@/components/market-pulse/MarketPulsePanels";
import { DecorativeBackground } from "@/components/skill-analysis/DecorativeDoodles";
import { Card, CardTitle, StatTile, type StatTileProps } from "@/components/ui/playful";
import { requireUser } from "@/lib/auth";
import { getMarketPulse, lastSync, selectView, timeAgo, type MarketPulse } from "@/lib/marketPulse";

export const metadata: Metadata = { title: "Market Pulse — Skillaro" };

const PATH = "/market-pulse";

export default async function MarketPulsePage({ searchParams }: PageProps<"/market-pulse">) {
  const user = await requireUser(PATH);
  const firstName = user.full_name.trim().split(/\s+/)[0] ?? "";
  const { role, sector } = await searchParams;
  const result = await getMarketPulse();

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-page text-ink">
      <Navbar currentPath={PATH} />
      <DecorativeBackground />

      <main className="relative mx-auto max-w-[960px] px-4 py-6 sm:px-6 sm:py-8">
        {result.status === "ok" ? (
          <Dashboard data={result.data} firstName={firstName} role={first(role)} sector={first(sector)} />
        ) : (
          <>
            <MarketPulseHero firstName={firstName} />
            {result.status === "no-data" ? (
              <Notice title="No market data yet">
                <p>Job ads have not been collected and profiled yet.</p>
                <p className="mt-2 text-xs text-ink/60">{result.message}</p>
              </Notice>
            ) : (
              <Notice title="Market data can't be loaded right now">
                <p>The job market service isn&apos;t reachable. Please try again shortly.</p>
              </Notice>
            )}
          </>
        )}
      </main>

      <div className="relative">
        <Footer />
      </div>
    </div>
  );
}

function Dashboard({ data, firstName, role, sector }: { data: MarketPulse; firstName: string; role: string; sector: string }) {
  const selection = selectView(data, role, sector);
  const synced = lastSync(data.sources);
  const collected = data.sources.filter((source) => source.collected);
  const stats: StatTileProps[] = [
    {
      label: "Job ads collected",
      value: selection.ads.toLocaleString("en"),
      Icon: Database,
      tone: "bg-[#b4c2fe]",
      detail: `${selection.adsWithText.toLocaleString("en")} with readable text`,
    },
    {
      label: "Unique skills extracted",
      value: selection.skills.length.toLocaleString("en"),
      Icon: Cpu,
      tone: "bg-[#fff6ea]",
      detail: selection.label,
    },
    {
      label: "Active data sources",
      value: String(collected.length),
      Icon: Globe,
      tone: "bg-lime",
      detail: collected.map((source) => source.name).join(", "),
    },
    {
      label: "Last sync",
      value: synced ? timeAgo(synced) : "–",
      Icon: RefreshCw,
      tone: "bg-[#edddfc]",
      detail: synced ? new Date(synced).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : undefined,
    },
  ];

  return (
    <>
      <MarketPulseHero firstName={firstName} label={selection.label} />

      <Card>
        <CardTitle Icon={SlidersHorizontal}>Filter your job role</CardTitle>
        <MarketPulseFilters
          // A new selection (also via the browser's back button) resets the dropdowns to the URL.
          key={`${selection.role?.role ?? ""}|${selection.sector?.sector ?? ""}`}
          roles={data.roles.map(({ role, sectors, ads }) => ({ role, sectors, ads }))}
          sectors={data.sectors.map((s) => s.sector)}
          role={selection.role?.role ?? ""}
          sector={selection.sector?.sector ?? ""}
        />
        <SelectionPanel role={selection.role} roles={data.totals.roles} ads={data.totals.ads} />
      </Card>

      <Card className="mt-6">
        <CardTitle Icon={BarChart3}>Overview</CardTitle>
        <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          {stats.map((stat) => (
            <StatTile key={stat.label} {...stat} />
          ))}
        </div>
      </Card>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
        <TopSkillsCard selection={selection} />
        <div className="grid content-start gap-6">
          <DataSourcesCard sources={data.sources} />
          <DeadSkillsCard />
        </div>
      </div>
    </>
  );
}

function first(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? "";
}
