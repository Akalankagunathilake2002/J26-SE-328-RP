import { BarChart3, FileText, Star, Target, TrendingUp } from "lucide-react";

import type { OverviewMetrics } from "./types";

interface OverviewCardsProps {
  stats?: OverviewMetrics;
  loading?: boolean;
}

const defaultStats: OverviewMetrics = {
  overallReadiness: 0,
  readinessTrend: "No analyses yet",
  analysesCompleted: 0,
  analysesTrend: "Start your first analysis",
  topMatchingRole: "No roles\nevaluated",
  matchPercentage: 0,
  rolesExplored: 0,
  rolesTrend: "Information Technology — IT",
};

// Overview metrics panel with 4 neobrutalist summary cards driven by real history data
export function OverviewCards({ stats = defaultStats, loading = false }: OverviewCardsProps) {
  return (
    <div className="bg-white border-2 border-ink rounded-2xl p-5 sm:p-6 shadow-[4px_4px_0px_#000]">
      {/* Header with sparks */}
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="size-5 text-ink" />
        <h2 className="font-extrabold text-lg sm:text-xl text-ink">Overview</h2>
      </div>

      {/* Grid of 4 Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 sm:gap-4">
        {/* Card 1: Overall Readiness */}
        <div className="bg-[#b4c2fe] border-2 border-ink rounded-xl p-4 shadow-[3px_3px_0px_#000] flex flex-col justify-between min-h-[140px]">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold text-ink">Overall Readiness</span>
            <span className="size-6 rounded-md bg-white border-2 border-ink flex items-center justify-center shadow-[1px_1px_0px_#000]">
              <Star className="size-3.5 fill-ink text-ink" />
            </span>
          </div>
          <div className="my-2">
            {loading ? (
              <div className="h-9 w-20 bg-ink/10 rounded animate-pulse" />
            ) : (
              <span className="text-3xl sm:text-4xl font-black text-ink">
                {stats.overallReadiness}%
              </span>
            )}
          </div>
          <div className="flex items-center gap-1 text-xs font-bold text-emerald-800">
            <TrendingUp className="size-3.5 shrink-0" />
            <span>{stats.readinessTrend}</span>
          </div>
        </div>

        {/* Card 2: Analyses Completed */}
        <div className="bg-[#fff6ea] border-2 border-ink rounded-xl p-4 shadow-[3px_3px_0px_#000] flex flex-col justify-between min-h-[140px]">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold text-ink">Analyses Completed</span>
            <span className="size-6 rounded-md bg-white border-2 border-ink flex items-center justify-center shadow-[1px_1px_0px_#000]">
              <FileText className="size-3.5 text-ink" />
            </span>
          </div>
          <div className="my-2">
            {loading ? (
              <div className="h-9 w-16 bg-ink/10 rounded animate-pulse" />
            ) : (
              <span className="text-3xl sm:text-4xl font-black text-ink">
                {stats.analysesCompleted}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1 text-xs font-bold text-blue-600">
            <TrendingUp className="size-3.5 shrink-0" />
            <span>{stats.analysesTrend}</span>
          </div>
        </div>

        {/* Card 3: Top Matching Role */}
        <div className="bg-lime border-2 border-ink rounded-xl p-4 shadow-[3px_3px_0px_#000] flex flex-col justify-between min-h-[140px]">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold text-ink">Top Matching Role</span>
            <span className="size-6 rounded-md bg-white border-2 border-ink flex items-center justify-center shadow-[1px_1px_0px_#000]">
              <Star className="size-3.5 fill-sun text-ink" />
            </span>
          </div>
          <div className="my-1">
            {loading ? (
              <div className="h-6 w-28 bg-ink/10 rounded animate-pulse" />
            ) : (
              <p className="text-base sm:text-lg font-black text-[#4338ca] leading-tight whitespace-pre-line truncate">
                {stats.topMatchingRole}
              </p>
            )}
          </div>
          <div>
            <span className="bg-[#4f46e5] text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full inline-block shadow-[1px_1px_0px_#000]">
              {stats.matchPercentage}% match
            </span>
          </div>
        </div>

        {/* Card 4: Roles Explored */}
        <div className="bg-[#edddfc] border-2 border-ink rounded-xl p-4 shadow-[3px_3px_0px_#000] flex flex-col justify-between min-h-[140px]">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold text-ink">Roles Explored</span>
            <span className="size-6 rounded-md bg-white border-2 border-ink flex items-center justify-center shadow-[1px_1px_0px_#000]">
              <Target className="size-3.5 text-ink" />
            </span>
          </div>
          <div className="my-2">
            {loading ? (
              <div className="h-9 w-16 bg-ink/10 rounded animate-pulse" />
            ) : (
              <span className="text-3xl sm:text-4xl font-black text-ink">
                {stats.rolesExplored}
              </span>
            )}
          </div>
          <div className="text-xs font-bold text-ink/75 truncate">
            <span>{stats.rolesTrend}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
