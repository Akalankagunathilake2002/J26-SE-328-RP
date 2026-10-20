"use client";

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import { AlertTriangle, BarChart3, Briefcase, CheckCircle2, Download, Info, Loader2, MinusCircle, Settings, X } from "lucide-react";

import type { DetailedAnalysisResult } from "./types";
import { downloadCareerReadinessReport } from "@/lib/reportGenerator";

const emptySubscribe = () => () => { };

interface CareerReadinessResultModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: DetailedAnalysisResult | null;
  studentName?: string;
}

// Modal presenting qualitative readiness breakdown, circular score, and learning priorities
export function CareerReadinessResultModal({
  isOpen,
  onClose,
  data,
  studentName,
}: CareerReadinessResultModalProps) {
  const isClient = useSyncExternalStore(emptySubscribe, () => true, () => false);
  const [activeDataKey, setActiveDataKey] = useState<string>("");
  const [showAllMatched, setShowAllMatched] = useState(false);
  const [showAllMissing, setShowAllMissing] = useState(false);
  const [showAllPriorities, setShowAllPriorities] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // Reset toggles during render when opening a new analysis record without triggering cascading renders
  const currentKey = data ? `${data.analysisId}-${data.roleName}` : "";
  if (currentKey !== activeDataKey) {
    setActiveDataKey(currentKey);
    setShowAllMatched(false);
    setShowAllMissing(false);
    setShowAllPriorities(false);
    setDownloadError(null);
  }

  // Close modal when Escape key is pressed and lock body scroll
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }

    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Filter skills into matched and missing lists based on result status
  const { matchedList, missingList } = useMemo(() => {
    if (!data?.skills) {
      return { matchedList: [], missingList: [] };
    }
    const matched = data.skills.filter(
      (s) =>
        s.resultStatus === "SATISFIED" ||
        s.resultStatus === "COVERED" ||
        s.resultStatus === "PARTIALLY_COVERED" ||
        s.resultStatus === "PARTIAL" ||
        s.matchType === "EXACT" ||
        s.matchType === "RELATIONSHIP" ||
        s.matchType === "PARTIAL_RELATIONSHIP",
    );
    const missing = data.skills.filter(
      (s) =>
        s.resultStatus === "MISSING" ||
        s.resultStatus === "DEFICIENT" ||
        s.matchType === "MISSING",
    );
    return { matchedList: matched, missingList: missing };
  }, [data]);

  // Determine if evidence confidence affects readiness below 100%
  const hasConfidenceImpact = useMemo(() => {
    if (!data) return false;
    const score = Math.round(Number(data.readinessScore) || 0);
    if (score >= 100) return false;
    const hasPartialEvidence = data.skills?.some(
      (s) => s.evidenceConfidence !== undefined && s.evidenceConfidence < 0.999,
    );
    return Boolean(hasPartialEvidence || (data.missingCount === 0 && score < 100));
  }, [data]);

  // Triggers two-page print-ready report download
  const handleDownload = async () => {
    if (isDownloading || !data?.analysisId) return;
    setIsDownloading(true);
    setDownloadError(null);
    try {
      await downloadCareerReadinessReport(data.analysisId, data.roleName, studentName);
    } catch (err) {
      setDownloadError(
        err instanceof Error ? err.message : "Failed to generate report. Please try again.",
      );
    } finally {
      setIsDownloading(false);
    }
  };

  if (!isOpen || !data || !isClient) {
    return null;
  }

  // Circular donut score dimensions and calculations
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const roundedScore = Math.round(Number(data.readinessScore) || 0);
  const strokeDashoffset =
    circumference - (circumference * Math.min(100, Math.max(0, roundedScore))) / 100;

  // Determine qualitative tier label and star badge
  const tierBadge = data.tier
    ? data.tier.startsWith("★")
      ? data.tier
      : `★ ${data.tier.toUpperCase()}`
    : "★ MODERATE";

  // Display first 4 items by default
  const visibleMatched = showAllMatched ? matchedList : matchedList.slice(0, 4);
  const visibleMissing = showAllMissing ? missingList : missingList.slice(0, 4);
  const visiblePriorities = showAllPriorities ? data.prioritySkills : data.prioritySkills.slice(0, 4);

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="career-readiness-result-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 md:p-6 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      {/* Modal Dialog Window */}
      <div
        className="relative w-full max-w-4xl max-h-[90vh] bg-page border-2 sm:border-[2.5px] border-ink rounded-3xl shadow-[8px_8px_0px_#000] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Lavender Neobrutalist Header Bar */}
        <div className="bg-[#edddfc] border-b-2 sm:border-b-[2.5px] border-ink px-4 sm:px-6 py-2.5 sm:py-3 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5 sm:gap-3">
            <span className="size-8 sm:size-9 rounded-xl bg-[#67e8f9] border-2 border-ink flex items-center justify-center shadow-[2px_2px_0px_#000] shrink-0">
              <BarChart3 className="size-4.5 sm:size-5 text-ink stroke-[2.5]" />
            </span>
            <div className="flex flex-col">
              <h2
                id="career-readiness-result-title"
                className="font-black text-sm sm:text-base tracking-wide text-ink uppercase leading-tight"
              >
                Career Readiness Result
              </h2>
              <div className="flex items-center gap-1.5 text-[11px] sm:text-xs text-ink/75 font-semibold mt-0.5">
                <Briefcase className="size-3 shrink-0 text-ink/70" />
                <span>
                  {data.roleName} {data.careerLevel ? `— ${data.careerLevel}` : ""}
                </span>
              </div>
            </div>
          </div>

          {/* Close Icon Button */}
          <button
            type="button"
            onClick={onClose}
            aria-label="Close modal"
            className="size-8 sm:size-9 rounded-xl bg-white hover:bg-red-100 text-ink border-2 border-ink flex items-center justify-center shadow-[2px_2px_0px_#000] transition-all hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[1px_1px_0px_#000] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none cursor-pointer shrink-0"
          >
            <X className="size-4 sm:size-4.5 text-ink stroke-[2.5]" />
          </button>
        </div>

        {/* Scrollable Modal Content */}
        <div className="p-3.5 sm:p-5 flex-1 min-h-0 overflow-y-auto flex flex-col gap-3 sm:gap-4">
          {/* Top Section: Score Donut Card + Why This Score & Stats */}
          <div className="grid grid-cols-1 md:grid-cols-[200px_1fr] gap-3 sm:gap-4 items-stretch">
            {/* Donut Score Card */}
            <div className="bg-white border-2 border-ink rounded-2xl p-4 shadow-[3px_3px_0px_#000] flex flex-col items-center justify-center text-center">
              {/* Circular SVG Donut Gauge */}
              <div className="relative size-28 sm:size-32 flex items-center justify-center">
                <svg className="size-full -rotate-90" viewBox="0 0 110 110">
                  <circle cx="55" cy="55" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="9" />
                  <circle
                    cx="55"
                    cy="55"
                    r={radius}
                    fill="none"
                    stroke="#006ee9"
                    strokeWidth="9"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    className="transition-all duration-700 ease-out"
                  />
                </svg>
                {/* Center Score Label */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="font-black text-2xl sm:text-3xl text-ink leading-none">
                    {roundedScore}%
                  </span>
                  <span className="text-[9px] sm:text-[10px] font-extrabold tracking-widest text-muted uppercase mt-0.5">
                    Readiness
                  </span>
                </div>
              </div>

              {/* Qualitative Status Badge */}
              <span className="bg-lime border-2 border-ink rounded-full px-3 py-0.5 text-[10px] sm:text-[11px] font-black text-ink shadow-[1px_1px_0px_#000] mt-2">
                {tierBadge}
              </span>

              {/* Baseline Readiness Score Indicator */}
              {data.baselineReadinessScore !== undefined && (
                <span className="text-[10px] sm:text-[11px] font-bold text-muted mt-1.5">
                  Baseline: {data.baselineReadinessScore}% (exact matches)
                </span>
              )}
            </div>

            {/* Why This Score Card & 3 Summary Badges */}
            <div className="flex flex-col gap-3">
              {/* Why This Score Card */}
              <div className="bg-[#dbeafe] border-2 border-ink rounded-2xl p-3.5 shadow-[3px_3px_0px_#000]">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <span className="size-4.5 rounded-full bg-[#3b82f6] border border-ink text-white flex items-center justify-center shrink-0">
                    <Info className="size-2.5 stroke-[3]" />
                  </span>
                  <h3 className="font-black text-[11px] sm:text-xs text-ink tracking-wider uppercase">
                    Why this score?
                  </h3>
                </div>
                <p className="text-xs sm:text-[13px] text-ink/85 font-medium leading-relaxed">
                  {data.explanation}
                </p>
              </div>

              {/* 3 Summary Badges */}
              <div className="grid grid-cols-3 gap-2.5">
                {/* Matched Summary */}
                <div className="bg-[#d9f99d] border-2 border-ink rounded-xl p-2.5 shadow-[2px_2px_0px_#000] flex items-center gap-2 sm:gap-2.5">
                  <span className="size-7 sm:size-7.5 rounded-lg bg-white border-2 border-ink flex items-center justify-center shrink-0 shadow-[1px_1px_0px_#000]">
                    <CheckCircle2 className="size-3.5 sm:size-4 text-ink" />
                  </span>
                  <div className="flex flex-col min-w-0">
                    <span className="text-[9px] sm:text-[10px] font-extrabold uppercase tracking-wider text-ink/70 truncate">
                      Matched Skills
                    </span>
                    <span className="text-xs sm:text-sm font-black text-ink leading-tight truncate">
                      {data.matchedCount ?? matchedList.length} Skills
                    </span>
                  </div>
                </div>

                {/* Missing Summary */}
                <div className="bg-[#fef08a] border-2 border-ink rounded-xl p-2.5 shadow-[2px_2px_0px_#000] flex items-center gap-2 sm:gap-2.5">
                  <span className="size-7 sm:size-7.5 rounded-lg bg-white border-2 border-ink flex items-center justify-center shrink-0 shadow-[1px_1px_0px_#000]">
                    <AlertTriangle className="size-3.5 sm:size-4 text-ink" />
                  </span>
                  <div className="flex flex-col min-w-0">
                    <span className="text-[9px] sm:text-[10px] font-extrabold uppercase tracking-wider text-ink/70 truncate">
                      Skill Gaps
                    </span>
                    <span className="text-xs sm:text-sm font-black text-ink leading-tight truncate">
                      {data.missingCount} Missing
                    </span>
                  </div>
                </div>

                {/* Analyzed Total Summary */}
                <div className="bg-[#f5d0fe] border-2 border-ink rounded-xl p-2.5 shadow-[2px_2px_0px_#000] flex items-center gap-2.5">
                  <span className="size-7 sm:size-7.5 rounded-lg bg-white border-2 border-ink flex items-center justify-center shrink-0 shadow-[1px_1px_0px_#000]">
                    <Settings className="size-3.5 sm:size-4 text-ink" />
                  </span>
                  <div className="flex flex-col min-w-0">
                    <span className="text-[9px] sm:text-[10px] font-extrabold uppercase tracking-wider text-ink/70 truncate">
                      Assessed
                    </span>
                    <span className="text-xs sm:text-sm font-black text-ink leading-tight truncate">
                      {data.totalRequirements} Total
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Section: 3 Skill Detail Columns */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-stretch">
            {/* Column 1: Matched Skills */}
            <div className="bg-white border-2 border-ink rounded-2xl p-3.5 shadow-[3px_3px_0px_#000] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-1.5 mb-1">
                  <div className="flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-emerald-500 border border-ink" />
                    <h4 className="font-black text-[11px] sm:text-xs tracking-wide text-ink uppercase">
                      Matched Skills
                    </h4>
                  </div>
                  <span className="bg-[#d9f99d] border-2 border-ink rounded px-1.5 py-0.5 text-[10px] font-black text-ink shadow-[1px_1px_0px_#000]">
                    {data.matchedCount ?? matchedList.length}
                  </span>
                </div>
                <p className="text-[10px] sm:text-[11px] text-muted font-medium mb-2.5">
                  Requirements matched in your profile:
                </p>

                {/* Skill List */}
                <div className="flex flex-col gap-1.5">
                  {visibleMatched.length === 0 ? (
                    <span className="text-xs text-muted">No matched skills recorded.</span>
                  ) : (
                    visibleMatched.map((skill) => (
                      <div
                        key={skill.id}
                        className="flex items-center gap-1.5 text-xs font-bold text-ink"
                      >
                        <CheckCircle2 className="size-3.5 text-emerald-600 fill-emerald-100 shrink-0" />
                        <span className="truncate" title={skill.requiredSkillName}>
                          {skill.requiredSkillName}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Show more / Show less toggle */}
              {matchedList.length > 4 && (
                <button
                  type="button"
                  onClick={() => setShowAllMatched((prev) => !prev)}
                  className="text-[11px] text-muted hover:text-ink font-bold cursor-pointer mt-2.5 text-left transition-colors"
                >
                  {showAllMatched ? "Show less" : "Show more"}
                </button>
              )}
            </div>

            {/* Column 2: Missing Skills */}
            <div className="bg-white border-2 border-ink rounded-2xl p-3.5 shadow-[3px_3px_0px_#000] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-1.5 mb-1">
                  <div className="flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-amber-400 border border-ink" />
                    <h4 className="font-black text-[11px] sm:text-xs tracking-wide text-ink uppercase">
                      Missing Skills
                    </h4>
                  </div>
                  <span className="bg-[#fef08a] border-2 border-ink rounded px-1.5 py-0.5 text-[10px] font-black text-ink shadow-[1px_1px_0px_#000]">
                    {data.missingCount}
                  </span>
                </div>
                <p className="text-[10px] sm:text-[11px] text-muted font-medium mb-2.5">
                  Important skills not found:
                </p>

                {/* Missing Skill List */}
                <div className="flex flex-col gap-1.5">
                  {visibleMissing.length === 0 ? (
                    <span className="text-xs text-emerald-700 font-bold">No missing skill gaps!</span>
                  ) : (
                    visibleMissing.map((skill) => (
                      <div
                        key={skill.id}
                        className="flex items-center gap-1.5 text-xs font-bold text-ink"
                      >
                        <MinusCircle className="size-3.5 text-amber-500 fill-amber-100 shrink-0" />
                        <span className="truncate" title={skill.requiredSkillName}>{skill.requiredSkillName}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Show more / Show less toggle */}
              {missingList.length > 4 && (
                <button
                  type="button"
                  onClick={() => setShowAllMissing((prev) => !prev)}
                  className="text-[11px] text-muted hover:text-ink font-bold cursor-pointer mt-2.5 text-left transition-colors"
                >
                  {showAllMissing ? "Show less" : "Show more"}
                </button>
              )}
            </div>

            {/* Column 3: Priority To Improve */}
            <div className="bg-white border-2 border-ink rounded-2xl p-3.5 shadow-[3px_3px_0px_#000] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-1.5 mb-1">
                  <div className="flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-purple-400 border border-ink" />
                    <h4 className="font-black text-[11px] sm:text-xs tracking-wide text-ink uppercase">
                      Priority to Improve
                    </h4>
                  </div>
                  <span className="bg-[#edddfc] border-2 border-ink rounded px-1.5 py-0.5 text-[10px] font-black text-ink shadow-[1px_1px_0px_#000]">
                    {data.prioritySkills.length > 0 ? "TOP" : "NONE"}
                  </span>
                </div>
                <p className="text-[10px] sm:text-[11px] text-muted font-medium mb-2.5">
                  {data.prioritySkills.length > 0 ? "Focus on these to boost score:" : "Priority recommendations:"}
                </p>

                {/* Ranked Priority List or Empty State */}
                <div className="flex flex-col gap-1.5">
                  {visiblePriorities.length === 0 ? (
                    <div className="p-2.5 rounded-xl bg-purple-50 border border-purple-200 text-xs text-purple-900 flex flex-col gap-1">
                      <div className="font-extrabold text-[11px] text-purple-900 flex items-center gap-1.5">
                        <Info className="size-3.5 text-purple-700 shrink-0" />
                        <span>No Priority Skills Identified</span>
                      </div>
                      <p className="text-[10.5px] text-purple-800/90 leading-relaxed font-normal">
                        {roundedScore < 100 && hasConfidenceImpact
                          ? "No explicit priority skills were identified. Readiness is influenced by evidence confidence across your skills—strengthening verification through coursework, projects, or assessments will help increase your score."
                          : "No explicit priority skills were identified for this role."}
                      </p>
                    </div>
                  ) : (
                    visiblePriorities.map((item) => (
                      <div
                        key={item.skillId}
                        className="flex items-center gap-2 text-xs font-bold text-ink"
                      >
                        <span className="size-5 rounded bg-[#f5d0fe] border-2 border-ink text-[10px] font-black text-ink flex items-center justify-center shadow-[1px_1px_0px_#000] shrink-0">
                          {item.priorityRank}
                        </span>
                        <span className="truncate" title={item.skillName}>{item.skillName}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Show more / Show less toggle */}
              {data.prioritySkills.length > 4 && (
                <button
                  type="button"
                  onClick={() => setShowAllPriorities((prev) => !prev)}
                  className="text-[11px] text-muted hover:text-ink font-bold cursor-pointer mt-2.5 text-left transition-colors"
                >
                  {showAllPriorities ? "Show less" : "Show more"}
                </button>
              )}
            </div>
          </div>

          {/* Download Error Alert if any */}
          {downloadError && (
            <div className="p-2.5 bg-red-50 border border-red-200 rounded-xl text-xs font-bold text-red-700">
              {downloadError}
            </div>
          )}
        </div>

        {/* Modal Footer Action Buttons (pinned at bottom, non-overlapping) */}
        <div className="border-t-2 sm:border-t-[2.5px] border-ink bg-white/90 backdrop-blur-xs px-4 sm:px-6 py-2.5 sm:py-3 flex items-center justify-between gap-3 shrink-0">
          {/* Active Download Report Action */}
          <button
            type="button"
            disabled={isDownloading}
            onClick={handleDownload}
            className="bg-lime hover:bg-[#bef264] text-ink border-2 border-ink rounded-xl px-4 py-2 shadow-[2px_2px_0px_#000] font-black text-xs flex items-center gap-1.5 hover:-translate-y-0.5 active:translate-y-0 transition-all cursor-pointer disabled:opacity-50 select-none"
            title="Download printable two-page Career Readiness Report"
          >
            {isDownloading ? (
              <>
                <Loader2 className="size-3.5 animate-spin text-ink" />
                <span>GENERATING REPORT...</span>
              </>
            ) : (
              <>
                <Download className="size-3.5 text-ink" />
                <span>DOWNLOAD REPORT</span>
              </>
            )}
          </button>

          {/* Close Button */}
          <button
            type="button"
            onClick={onClose}
            className="bg-white hover:bg-gray-100 text-ink border-2 border-ink rounded-xl px-4 py-2 shadow-[2px_2px_0px_#000] font-bold text-xs hover:-translate-y-0.5 active:translate-y-0 transition-all cursor-pointer"
          >
            CLOSE
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

