// Re-export shared analysis types and utilities from readinessApi
export type {
  TargetRoleOption,
  OverviewMetrics,
  ReadinessSkillResult,
  ReadinessPrioritySkill,
  DetailedAnalysisResult,
  AnalysisHistoryItem,
} from "@/lib/readinessApi";

export {
  formatCareerLevel,
  formatAnalysisDate,
  deriveOverviewStats,
  fetchDetailedAnalysisResult,
} from "@/lib/readinessApi";

export interface AnalysisHistoryRecord {
  id: string;
  role: string;
  careerLevel: string;
  readinessScore: number;
  date: string;
}
