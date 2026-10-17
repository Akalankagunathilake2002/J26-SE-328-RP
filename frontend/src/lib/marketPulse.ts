import "server-only";

// Market Pulse data from the job-market-intelligence-engine service, through the API gateway.
// The service reads the skill profile built from collected job ads (topjobs.lk for now).
const API_GATEWAY_URL = process.env.API_GATEWAY_URL ?? "http://localhost:8080";

export type SkillDemand = {
  skill: string;
  category: string;
  ssk_id: string | null;
  ads: number; // ads asking for the skill
  share: number; // of the ads with readable text, 0–1
};

export type SectorProfile = {
  sector: string;
  ads: number;
  ads_with_text: number;
  skills: SkillDemand[];
};

export type RoleProfile = {
  role: string;
  mapped: boolean;
  sectors: string[];
  ads: number;
  ads_with_text: number;
  titles: string[];
  seniority: Record<string, number>;
  experience: Record<string, number>;
  skills: SkillDemand[];
  flags: Record<string, number>;
};

export type Source = {
  site: string;
  name: string;
  url: string;
  collected: boolean;
  reason: string | null;
  ads: number;
  last_collected: string | null;
  last_checked: string | null;
};

export type MarketPulse = {
  generated_at: string;
  ad_statuses: string[];
  sources: Source[];
  totals: { ads: number; ads_with_text: number; roles: number; unmapped_roles: number; unique_skills: number };
  sectors: SectorProfile[];
  skills: SkillDemand[];
  roles: RoleProfile[];
};

export type MarketPulseResult =
  | { status: "ok"; data: MarketPulse }
  | { status: "no-data"; message: string } // the service is up, but no ads have been profiled yet
  | { status: "unavailable" };

export async function getMarketPulse(): Promise<MarketPulseResult> {
  let response: Response;
  try {
    response = await fetch(`${API_GATEWAY_URL}/jobs/market-pulse`, { cache: "no-store" });
  } catch {
    return { status: "unavailable" };
  }
  if (response.status === 404) {
    const detail = (await response.json().catch(() => null))?.detail;
    // The gateway answers "Not found" when the service isn't routed yet.
    if (typeof detail === "string" && detail !== "Not found") return { status: "no-data", message: detail };
  }
  if (!response.ok) return { status: "unavailable" };
  return { status: "ok", data: (await response.json()) as MarketPulse };
}

/** What the filters select: one role, all roles of one sector, or everything. */
export type Selection = {
  role: RoleProfile | null;
  sector: SectorProfile | null;
  label: string;
  ads: number;
  adsWithText: number;
  skills: SkillDemand[];
};

export function selectView(data: MarketPulse, roleName?: string, sectorName?: string): Selection {
  const sector = data.sectors.find((s) => s.sector === sectorName) ?? null;
  const role = data.roles.find((r) => r.role === roleName && (!sector || r.sectors.includes(sector.sector))) ?? null;
  if (role) {
    return { role, sector, label: role.role, ads: role.ads, adsWithText: role.ads_with_text, skills: role.skills };
  }
  if (sector) {
    return {
      role,
      sector,
      label: `All ${sector.sector} roles`,
      ads: sector.ads,
      adsWithText: sector.ads_with_text,
      skills: sector.skills,
    };
  }
  return {
    role,
    sector,
    label: "All roles",
    ads: data.totals.ads,
    adsWithText: data.totals.ads_with_text,
    skills: data.skills,
  };
}

/** When the newest data was collected or checked, across the collected sites. */
export function lastSync(sources: Source[]): string | null {
  const times = sources.flatMap((s) => [s.last_checked, s.last_collected]).filter((t): t is string => Boolean(t));
  return times.length ? times.reduce((a, b) => (Date.parse(a) > Date.parse(b) ? a : b)) : null;
}

/** "just now", "5m ago", "2h ago", "3d ago". */
export function timeAgo(iso: string): string {
  const minutes = Math.max(0, Math.floor((Date.now() - Date.parse(iso)) / 60_000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
