import Link from "next/link";

import { ArrowRightIcon } from "@/components/icons";
import { getMarketPulse, type MarketPulseResult, type SkillDemand } from "@/lib/marketPulse";

import { Reveal } from "./Reveal";

type Row = { skill: string; share: number };

type Teaser = {
  live: boolean;
  sources: string;
  sectors: { sector: string; ads: number }[];
  top: Row[];
  technical: Row[];
};

/** The skill ranking from the 22 Oct 2026 sync, used when the job market service isn't running. The page
 *  shows rankings only, never figures (ads counts, percentages or dates). */
const SNAPSHOT: Teaser = {
  live: false,
  sources: "topjobs.lk and itpro.lk",
  sectors: [
    { sector: "IT", ads: 73 },
    { sector: "Management", ads: 69 },
    { sector: "HR", ads: 50 },
    { sector: "Agriculture", ads: 35 },
  ],
  top: [
    { skill: "Communication", share: 0.66 },
    { skill: "Coordination & planning", share: 0.335 },
    { skill: "Report writing & documentation", share: 0.335 },
    { skill: "Working independently", share: 0.274 },
    { skill: "Analytical thinking", share: 0.245 },
    { skill: "Problem solving", share: 0.226 },
  ],
  technical: [
    { skill: "Microsoft Office", share: 0.184 },
    { skill: "Microsoft Excel", share: 0.142 },
    { skill: "REST APIs", share: 0.08 },
    { skill: "IT support & troubleshooting", share: 0.075 },
    { skill: "CI/CD", share: 0.071 },
    { skill: "Git", share: 0.071 },
  ],
};

const SITE_NAMES: Record<string, string> = { topjobs: "topjobs.lk", itpro: "itpro.lk" };

function rows(skills: SkillDemand[], keep: (s: SkillDemand) => boolean): Row[] {
  return skills.filter(keep).slice(0, 6).map(({ skill, share }) => ({ skill, share }));
}

async function loadTeaser(): Promise<Teaser> {
  // Don't hold the home page up if the service is slow: fall back to the snapshot after 1.5 s.
  const timeout = new Promise<MarketPulseResult>((resolve) => setTimeout(() => resolve({ status: "unavailable" }), 1500));
  const result = await Promise.race([getMarketPulse(), timeout]);
  if (result.status !== "ok") return SNAPSHOT;
  const { data } = result;
  const collected = data.sources.filter((s) => s.collected && s.ads > 0);
  return {
    live: true,
    sources: collected.map((s) => SITE_NAMES[s.site] ?? s.name).join(" and ") || SNAPSHOT.sources,
    sectors: data.sectors.map(({ sector, ads }) => ({ sector, ads })).sort((a, b) => b.ads - a.ads),
    top: rows(data.skills, (s) => s.category !== "Qualification"),
    technical: rows(data.skills, (s) => s.category === "Technical" || s.category === "Tool"),
  };
}

/** A dark band (like the Market Pulse sidebar) with what employers ask for most, from the real job ads. */
export async function MarketTeaser() {
  const t = await loadTeaser();

  return (
    <section aria-labelledby="market-teaser-heading" className="mt-16 bg-[#17161d] text-white">
      <div className="mx-auto grid max-w-[1240px] gap-10 px-4 py-14 sm:px-8 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:gap-14 lg:py-16">
        <Reveal className="flex flex-col justify-center">
          <p className="inline-flex items-center gap-2 self-start rounded-full border border-white/15 bg-white/5 px-3 py-1 text-[12.5px] font-bold text-[#d0ffa4]">
            <span aria-hidden="true" className="relative flex size-2">
              {t.live && <span className="absolute inline-flex size-full animate-ping rounded-full bg-[#d0ffa4] opacity-60 motion-reduce:animate-none" />}
              <span className="relative inline-flex size-2 rounded-full bg-[#d0ffa4]" />
            </span>
            {t.live ? "Live from real job ads" : "From real job ads"}
          </p>
          <h2 id="market-teaser-heading" className="mt-4 font-editorial text-[clamp(32px,3.6vw,46px)] font-semibold leading-[1.08] tracking-[-0.01em]">
            What employers ask for <em className="text-[#d0ffa4]">right now.</em>
          </h2>
          <p className="mt-3 max-w-[460px] text-[16.5px] text-white/70">
            We read real job ads from {t.sources} every day and turn them into the skills each role needs.
          </p>

          {/* No figures here on purpose (Akalanka's request): what it does, not how many ads it has read. */}
          <ul className="mt-6 grid max-w-[460px] gap-2.5 sm:grid-cols-3">
            {[
              { title: "Updated daily", text: "New ads every morning" },
              { title: "Skills by role", text: "What each job asks for" },
              { title: "Every sector", text: "Not only IT" },
            ].map(({ title, text }) => (
              <li key={title} className="rounded-2xl bg-white/[0.06] px-3.5 py-3 ring-1 ring-white/10">
                <p className="font-editorial text-[17px] font-semibold leading-tight text-white">{title}</p>
                <p className="mt-0.5 text-[12.5px] text-white/60">{text}</p>
              </li>
            ))}
          </ul>

          <ul aria-label="Sectors covered" className="mt-4 flex flex-wrap gap-2 text-[13px] font-semibold">
            {t.sectors.map(({ sector }) => (
              <li key={sector} className="rounded-full bg-white/[0.08] px-3 py-1 text-white/85">
                {sector}
              </li>
            ))}
          </ul>

          <Link
            href="/market-pulse"
            className="mt-7 inline-flex min-h-12 items-center gap-2 self-start rounded-full bg-[#d0ffa4] px-6 text-[16px] font-bold text-[#17161d] transition hover:-translate-y-0.5 hover:bg-[#c2f78f] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#d0ffa4]/40"
          >
            Open Market Pulse
            <ArrowRightIcon className="size-[18px]" strokeWidth={2.4} />
          </Link>
        </Reveal>

        <div className="grid gap-4 sm:grid-cols-2">
          <Reveal delay={120}>
            <SkillList title="Most asked-for skills" note="Across all job ads" rows={t.top} bar="bg-[#d0ffa4]" />
          </Reveal>
          <Reveal delay={260}>
            <SkillList title="Top technical skills" note="Tools and technical skills only" rows={t.technical} bar="bg-[#eba0ff]" />
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function SkillList({ title, note, rows, bar }: { title: string; note: string; rows: Row[]; bar: string }) {
  const max = Math.max(...rows.map((r) => r.share), 0.01);
  return (
    <div className="h-full rounded-[22px] bg-white/[0.05] p-5 ring-1 ring-white/10">
      <h3 className="font-editorial text-[20px] font-semibold">{title}</h3>
      <p className="text-[13px] text-white/55">{note}</p>
      <ol className="mt-4 space-y-3.5">
        {rows.map((r, i) => (
          <li key={r.skill}>
            <p className="truncate text-[14.5px] font-semibold">
              <span className="mr-1.5 text-white/40">{i + 1}</span>
              {r.skill}
            </p>
            {/* Relative length only (the top skill is full width); no figures are shown. */}
            <div aria-hidden="true" className="mt-1.5 h-1.5 rounded-full bg-white/10">
              <div className={`h-full rounded-full ${bar}`} style={{ width: `${(r.share / max) * 100}%` }} />
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
