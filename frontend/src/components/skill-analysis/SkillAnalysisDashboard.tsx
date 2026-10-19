"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { CareerReadinessResultModal } from "./CareerReadinessResultModal";
import { HeroSection } from "./HeroSection";
import { OverviewCards } from "./OverviewCards";
import { ProgressAndMatches } from "./ProgressAndMatches";
import { RecentAnalysisHistory } from "./RecentAnalysisHistory";
import { StartAnalysisPanel } from "./StartAnalysisPanel";
import {
  deriveOverviewStats,
  fetchDetailedAnalysisResult,
  type DetailedAnalysisResult,
} from "./types";
import { readinessApi, type AnalysisHistoryItem } from "@/lib/readinessApi";

interface SkillAnalysisDashboardProps {
  userId: string;
  firstName: string;
}

// Master coordinator connecting target role selection, history, overview, and result modals
export function SkillAnalysisDashboard({ userId, firstName }: SkillAnalysisDashboardProps) {
  const [historyItems, setHistoryItems] = useState<AnalysisHistoryItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const [activeResult, setActiveResult] = useState<DetailedAnalysisResult | null>(null);
  const [isResultModalOpen, setIsResultModalOpen] = useState(false);

  // Fetch paginated analysis history for the current authenticated user
  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const response = await readinessApi.listAnalyses({
        user_id: userId,
        limit: 10,
        offset: 0,
      });
      setHistoryItems(response.items || []);
      setTotalCount(response.total ?? (response.items?.length || 0));
    } catch (err) {
      setHistoryError(
        err instanceof Error ? err.message : "Failed to load past analysis history.",
      );
    } finally {
      setHistoryLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    let ignore = false;
    readinessApi
      .listAnalyses({
        user_id: userId,
        limit: 10,
        offset: 0,
      })
      .then((response) => {
        if (ignore) return;
        setHistoryItems(response.items || []);
        setTotalCount(response.total ?? (response.items?.length || 0));
        setHistoryLoading(false);
      })
      .catch((err) => {
        if (ignore) return;
        setHistoryError(
          err instanceof Error ? err.message : "Failed to load past analysis history.",
        );
        setHistoryLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [userId]);

  // Derive overview cards metrics dynamically from real history records
  const overviewStats = useMemo(() => {
    return deriveOverviewStats(historyItems, totalCount);
  }, [historyItems, totalCount]);

  // Called when a new analysis completes successfully from the StartAnalysisPanel
  const handleAnalysisSuccess = (analysisId: string, result: DetailedAnalysisResult) => {
    // Refresh history and overview statistics
    fetchHistory();
    // Open detailed results modal
    setActiveResult(result);
    setIsResultModalOpen(true);
  };

  // Open detailed report modal for any historical analysis record
  const handleViewResult = async (analysisId: string) => {
    try {
      const result = await fetchDetailedAnalysisResult(analysisId);
      setActiveResult(result);
      setIsResultModalOpen(true);
    } catch (err) {
      setHistoryError(
        err instanceof Error ? err.message : "Failed to load detailed analysis report.",
      );
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <HeroSection firstName={firstName} />
        <StartAnalysisPanel userId={userId} onAnalysisSuccess={handleAnalysisSuccess} />
      </div>

      <OverviewCards stats={overviewStats} loading={historyLoading} />

      <ProgressAndMatches />

      <RecentAnalysisHistory
        userId={userId}
        items={historyItems}
        total={totalCount}
        loading={historyLoading}
        error={historyError}
        onRefresh={fetchHistory}
        onViewDetails={handleViewResult}
      />

      {/* Shared Results Modal */}
      <CareerReadinessResultModal
        isOpen={isResultModalOpen}
        onClose={() => setIsResultModalOpen(false)}
        data={activeResult}
      />
    </div>
  );
}
