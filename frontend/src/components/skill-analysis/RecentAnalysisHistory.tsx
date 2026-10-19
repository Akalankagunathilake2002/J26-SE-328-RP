"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Briefcase, Clock, FileText, Loader2, RefreshCw } from "lucide-react";

import { CareerReadinessResultModal } from "./CareerReadinessResultModal";
import {
  fetchDetailedAnalysisResult,
  formatAnalysisDate,
  formatCareerLevel,
  type DetailedAnalysisResult,
} from "./types";
import { readinessApi, type AnalysisHistoryItem } from "@/lib/readinessApi";

interface RecentAnalysisHistoryProps {
  userId?: string;
  items?: AnalysisHistoryItem[];
  total?: number;
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onViewDetails?: (analysisId: string) => void;
}

// Recent Analysis History table populated with real analysis records
export function RecentAnalysisHistory({
  userId,
  items: propItems,
  loading: propLoading,
  error: propError,
  onRefresh,
  onViewDetails,
}: RecentAnalysisHistoryProps = {}) {
  // Internal state for self-fetching when used without parent controller
  const [internalItems, setInternalItems] = useState<AnalysisHistoryItem[]>([]);
  const [internalLoading, setInternalLoading] = useState(false);
  const [internalError, setInternalError] = useState<string | null>(null);

  // Result modal state for view actions
  const [selectedResult, setSelectedResult] = useState<DetailedAnalysisResult | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loadingRowId, setLoadingRowId] = useState<string | null>(null);

  const isControlled = propItems !== undefined;
  const items = isControlled ? propItems : internalItems;
  const loading = isControlled ? Boolean(propLoading) : internalLoading;
  const error = isControlled ? propError : internalError;

  // Self-fetch records if component is mounted standalone with userId
  const fetchStandaloneHistory = () => {
    if (!userId || isControlled) return;
    setInternalLoading(true);
    setInternalError(null);
    readinessApi
      .listAnalyses({ user_id: userId, limit: 10, offset: 0 })
      .then((res) => {
        setInternalItems(res.items || []);
      })
      .catch((err) => {
        setInternalError(err instanceof Error ? err.message : "Failed to load analysis history.");
      })
      .finally(() => {
        setInternalLoading(false);
      });
  };

  useEffect(() => {
    if (isControlled || !userId) return;

    let ignore = false;
    readinessApi
      .listAnalyses({ user_id: userId, limit: 10, offset: 0 })
      .then((res) => {
        if (ignore) return;
        setInternalItems(res.items || []);
        setInternalLoading(false);
      })
      .catch((err) => {
        if (ignore) return;
        setInternalError(err instanceof Error ? err.message : "Failed to load analysis history.");
        setInternalLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [userId, isControlled]);

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    } else {
      fetchStandaloneHistory();
    }
  };

  // Open detailed analysis report for a selected record
  const handleView = async (item: AnalysisHistoryItem) => {
    const analysisId = item.analysis_id || item.analysisId;
    if (!analysisId) return;

    if (onViewDetails) {
      onViewDetails(analysisId);
      return;
    }

    setLoadingRowId(analysisId);
    try {
      const result = await fetchDetailedAnalysisResult(analysisId);
      setSelectedResult(result);
      setIsModalOpen(true);
    } catch {
      // Fallback empty result shell on network error
    } finally {
      setLoadingRowId(null);
    }
  };

  return (
    <>
      <div className="bg-white border-2 border-ink rounded-2xl shadow-[4px_4px_0px_#000] overflow-hidden">
        {/* Lime Header Bar with Refresh / Status Action */}
        <div className="bg-lime border-b-2 border-ink px-5 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="size-5 text-ink" />
            <h3 className="font-extrabold text-base sm:text-lg text-ink">
              Recent Analysis History
            </h3>
          </div>
          <button
            type="button"
            onClick={handleRefresh}
            disabled={loading}
            className="bg-[#edddfc] hover:bg-[#dec2fa] text-ink font-bold text-xs px-3.5 py-1.5 rounded-lg border-2 border-ink shadow-[2px_2px_0px_#000] transition-all hover:-translate-y-0.5 active:translate-y-0 cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
            title="Refresh history records"
          >
            <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="p-4 bg-red-50 border-b border-red-200 flex items-center justify-between gap-3 text-xs sm:text-sm font-semibold text-red-800">
            <div className="flex items-center gap-2">
              <AlertCircle className="size-4 text-red-600 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              type="button"
              onClick={handleRefresh}
              className="text-xs font-black underline text-ink shrink-0 cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {/* Analysis Records Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[640px]">
            <thead>
              <tr className="border-b border-ink/10 bg-gray-50/60 text-[11px] font-bold text-muted uppercase tracking-wider">
                <th scope="col" className="px-5 py-3.5 text-left">
                  Role
                </th>
                <th scope="col" className="px-4 py-3.5 text-center">
                  Readiness Score
                </th>
                <th scope="col" className="px-4 py-3.5 text-center">
                  Date
                </th>
                <th scope="col" className="px-5 py-3.5 text-center">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink/10 text-sm">
              {loading && items.length === 0 ? (
                // Skeleton loading rows
                [1, 2, 3].map((idx) => (
                  <tr key={`skeleton-${idx}`} className="animate-pulse">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="size-8 rounded-lg bg-gray-200 border border-ink/20" />
                        <div className="space-y-1.5">
                          <div className="h-4 w-32 bg-gray-200 rounded" />
                          <div className="h-3 w-20 bg-gray-200 rounded" />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className="h-3 w-32 bg-gray-200 rounded-full mx-auto" />
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className="h-3 w-24 bg-gray-200 rounded mx-auto" />
                    </td>
                    <td className="px-5 py-4 text-center">
                      <div className="h-7 w-20 bg-gray-200 rounded mx-auto" />
                    </td>
                  </tr>
                ))
              ) : items.length === 0 ? (
                // Empty history state
                <tr>
                  <td colSpan={4} className="px-5 py-10 text-center text-muted">
                    <Briefcase className="size-8 mx-auto mb-2 text-ink/40" />
                    <p className="font-bold text-sm text-ink">No analyses found</p>
                    <p className="text-xs text-muted mt-1 max-w-sm mx-auto">
                      Select an industry role above and click &quot;Analyze Readiness&quot; to generate your first career readiness report.
                    </p>
                  </td>
                </tr>
              ) : (
                items.map((item) => {
                  const analysisId = item.analysis_id || item.analysisId;
                  const roleName = item.role_name || item.roleName || "Target Role";
                  const careerLevel = formatCareerLevel(item.career_level);
                  const score = Math.round(Number(item.readinessScore ?? item.readiness_score ?? 0));
                  const isRowLoading = loadingRowId === analysisId;

                  return (
                    <tr key={analysisId} className="hover:bg-cream/40 transition-colors">
                      {/* Role title and career level */}
                      <td className="px-5 py-4 text-left">
                        <div className="flex items-center gap-3">
                          <span className="size-8 rounded-lg border-2 border-ink bg-white flex items-center justify-center shadow-[1px_1px_0px_#000] shrink-0">
                            <Briefcase className="size-4 text-ink" />
                          </span>
                          <div className="flex flex-col text-left min-w-0">
                            <span className="font-extrabold text-ink text-sm leading-tight truncate">
                              {roleName}
                            </span>
                            <span className="text-xs text-muted font-semibold mt-0.5 leading-tight">
                              {careerLevel}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Readiness Score Progress Bar */}
                      <td className="px-4 py-4 text-center">
                        <div className="flex items-center justify-center gap-3">
                          <div className="w-28 sm:w-36 h-3 bg-[#e2e8f0] rounded-full overflow-hidden border border-ink/20">
                            <div
                              className="bg-[#006ee9] h-full rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                            />
                          </div>
                          <span className="text-sm font-black text-[#006ee9] min-w-[2.5rem]">
                            {score}%
                          </span>
                        </div>
                      </td>

                      {/* Evaluation Timestamp */}
                      <td className="px-4 py-4 text-center text-xs font-medium text-muted whitespace-nowrap">
                        {formatAnalysisDate(item.started_at || item.createdAt)}
                      </td>

                      {/* Actions */}
                      <td className="px-5 py-4 text-center">
                        <div className="inline-flex items-center justify-center gap-2">
                          <button
                            type="button"
                            disabled={isRowLoading}
                            onClick={() => handleView(item)}
                            className="bg-[#1e40af] hover:bg-[#1d4ed8] text-white text-[11px] font-bold px-3.5 py-1.5 rounded-lg border-2 border-ink shadow-[2px_2px_0px_#000] hover:-translate-y-0.5 active:translate-y-0 transition-all cursor-pointer whitespace-nowrap disabled:opacity-50 flex items-center gap-1"
                          >
                            {isRowLoading ? (
                              <>
                                <Loader2 className="size-3 animate-spin" />
                                <span>Loading...</span>
                              </>
                            ) : (
                              <span>View</span>
                            )}
                          </button>
                          <button
                            type="button"
                            disabled
                            title="Report download is coming soon"
                            className="bg-lime/70 text-ink/70 text-[11px] font-bold px-2.5 py-1.5 rounded-lg border-2 border-ink/40 shadow-[1px_1px_0px_#000] flex items-center gap-1.5 whitespace-nowrap cursor-not-allowed select-none shrink-0"
                          >
                            <FileText className="size-3.5 text-ink/70 shrink-0" />
                            <span>Download Report</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Standalone Result Modal */}
      <CareerReadinessResultModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        data={selectedResult}
      />
    </>
  );
}
