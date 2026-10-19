"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Briefcase,
  CheckCircle2,
  Download,
  FileText,
  Info,
  MinusCircle,
  Settings,
  X,
} from "lucide-react";

import type { DetailedAnalysisResult } from "./mockData";

interface CareerReadinessResultModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: DetailedAnalysisResult | null;
}

// Reusable modal presenting qualitative readiness breakdown, circular score, and learning priorities
export function CareerReadinessResultModal({
  isOpen,
  onClose,
  data,
}: CareerReadinessResultModalProps) {
  const [showAllMatched, setShowAllMatched] = useState(false);
  const [showAllMissing, setShowAllMissing] = useState(false);
  const [showAllPriorities, setShowAllPriorities] = useState(false);

  // Close modal when Escape key is pressed
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

  // Reset expansion toggles whenever modal opens with fresh data
  useEffect(() => {
    if (isOpen) {
      setShowAllMatched(false);
      setShowAllMissing(false);
      setShowAllPriorities(false);
    }
  }, [isOpen]);

  // Filter skills into matched and missing lists based on result status
  const { matchedList, missingList } = useMemo(() => {
    if (!data?.skills) {
      return { matchedList: [], missingList: [] };
    }
    const matched = data.skills.filter(
      (s) => s.resultStatus === "SATISFIED" || s.matchType === "EXACT" || s.matchType === "RELATIONSHIP"
    );
    const missing = data.skills.filter(
      (s) => s.resultStatus === "MISSING" || s.resultStatus === "DEFICIENT" || s.matchType === "MISSING"
    );
    return { matchedList: matched, missingList: missing };
  }, [data]);

  if (!isOpen || !data) {
    return null;
  }

  // Circular donut score dimensions and calculations
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset =
    circumference - (circumference * Math.min(100, Math.max(0, data.readinessScore))) / 100;

  // Determine qualitative tier label and star badge
  const tierBadge = data.tier === "EXCELLENT" ? "★ EXCELLENT" : data.tier === "GOOD" ? "★ GOOD" : "★ MODERATE";

  // Slice displayed items based on expansion state
  const visibleMatched = showAllMatched ? matchedList : matchedList.slice(0, 4);
  const remainingMatchedCount = matchedList.length - 4;

  const visibleMissing = showAllMissing ? missingList : missingList.slice(0, 4);
  const remainingMissingCount = missingList.length - 4;

  const visiblePriorities = showAllPriorities ? data.prioritySkills : data.prioritySkills.slice(0, 3);
  const hasRemainingPriorities = data.prioritySkills.length > 3;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="career-readiness-result-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 md:p-6 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      {/* Modal Dialog Window */}
      <div
        className="relative w-full max-w-4xl max-h-[92vh] bg-page border-2 sm:border-[2.5px] border-ink rounded-3xl shadow-[8px_8px_0px_#000] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Lavender Neobrutalist Header Bar */}
        <div className="bg-[#edddfc] border-b-2 sm:border-b-[2.5px] border-ink px-5 sm:px-7 py-3.5 sm:py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <span className="size-10 sm:size-11 rounded-xl bg-[#67e8f9] border-2 border-ink flex items-center justify-center shadow-[2px_2px_0px_#000] shrink-0">
              <BarChart3 className="size-5 sm:size-6 text-ink stroke-[2.5]" />
            </span>
            <div className="flex flex-col">
              <h2
                id="career-readiness-result-title"
                className="font-black text-base sm:text-xl tracking-wide text-ink uppercase leading-tight"
              >
                Career Readiness Result
              </h2>
              <div className="flex items-center gap-1.5 text-xs sm:text-sm text-ink/75 font-semibold mt-0.5">
                <Briefcase className="size-3.5 shrink-0 text-ink/70" />
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
            className="size-9 sm:size-10 rounded-xl bg-white hover:bg-red-100 text-ink border-2 border-ink flex items-center justify-center shadow-[2px_2px_0px_#000] transition-all hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[1px_1px_0px_#000] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none cursor-pointer shrink-0"
          >
            <X className="size-5 text-ink stroke-[2.5]" />
          </button>
        </div>

        {/* Scrollable Modal Content */}
        <div className="p-4 sm:p-6 md:p-7 flex flex-col gap-4 sm:gap-5 overflow-y-auto max-h-[calc(92vh-130px)]">
          {/* Top Section: Score Donut Card + Why This Score & Stats */}
          <div className="grid grid-cols-1 md:grid-cols-[230px_1fr] gap-4 sm:gap-5 items-stretch">
            {/* Donut Score Card */}
            <div className="bg-white border-2 border-ink rounded-2xl p-4 sm:p-5 shadow-[3px_3px_0px_#000] flex flex-col items-center justify-center text-center">
              {/* Circular SVG Donut Gauge */}
              <div className="relative size-36 sm:size-40 flex items-center justify-center">
                <svg className="size-full -rotate-90" viewBox="0 0 130 130">
                  {/* Track Circle */}
                  <circle cx="65" cy="65" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="11" />
                  {/* Progress Arc */}
                  <circle cx="65" cy="65" r={radius} fill="none" stroke="#006ee9" strokeWidth="11" strokeDasharray={circumference} strokeDashoffset={strokeDashoffset} strokeLinecap="round" className="transition-all duration-700 ease-out" />
                </svg>
                {/* Center Score Label */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="font-black text-2xl sm:text-3xl text-ink leading-none">
                    {data.readinessScore}%
                  </span>
                  <span className="text-[10px] sm:text-xs font-black tracking-widest text-muted uppercase mt-1">
                    Readiness
                  </span>
                </div>
              </div>

              {/* Qualitative Status Badge */}
              <span className="bg-lime border-2 border-ink rounded-full px-4 py-1 text-xs font-black text-ink shadow-[1px_1px_0px_#000] mt-3">
                {tierBadge}
              </span>

              {/* Baseline Readiness Score Indicator */}
              {data.baselineReadinessScore !== undefined && (
                <span className="text-[11px] font-bold text-muted mt-2">
                  Baseline: {data.baselineReadinessScore}% (exact matches)
                </span>
              )}
            </div>

            {/* Why This Score Card & 3 Summary Cards */}
            <div className="flex flex-col gap-3 sm:gap-4 justify-between">
              {/* Why This Score Card */}
              <div className="bg-[#dbeafe] border-2 border-ink rounded-2xl p-4 sm:p-5 shadow-[3px_3px_0px_#000]">
                <div className="flex items-center gap-2 mb-2">
                  <span className="size-5 rounded-full bg-[#3b82f6] border border-ink text-white flex items-center justify-center shrink-0">
                    <Info className="size-3 stroke-[3]" />
                  </span>
                  <h3 className="font-black text-xs sm:text-sm text-ink tracking-wider uppercase">
                    Why this score?
                  </h3>
                </div>
                <p className="text-xs sm:text-sm text-ink/85 font-medium leading-relaxed">
                  {data.explanation}
                </p>
              </div>

              {/* 3 Summary Badges */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* Matched Summary */}
                <div className="bg-[#d9f99d] border-2 border-ink rounded-xl p-3 shadow-[2px_2px_0px_#000] flex items-center gap-2.5">
                  <span className="size-8 rounded-lg bg-white border-2 border-ink flex items-center justify-center shrink-0 shadow-[1px_1px_0px_#000]">
                    <CheckCircle2 className="size-4 text-ink" />
                  </span>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-ink/75">
                      Matched
                    </span>
                    <span className="text-sm sm:text-base font-black text-ink leading-tight">
                      {data.satisfiedCount} Skills
                    </span>
                  </div>
                </div>

                {/* Missing Summary */}
                <div className="bg-[#fef08a] border-2 border-ink rounded-xl p-3 shadow-[2px_2px_0px_#000] flex items-center gap-2.5">
                  <span className="size-8 rounded-lg bg-white border-2 border-ink flex items-center justify-center shrink-0 shadow-[1px_1px_0px_#000]">
                    <AlertTriangle className="size-4 text-ink" />
                  </span>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-ink/75">
                      Missing
                    </span>
                    <span className="text-sm sm:text-base font-black text-ink leading-tight">
                      {data.missingCount} Skills
                    </span>
                  </div>
                </div>

                {/* Analyzed Total Summary */}
                <div className="bg-[#f5d0fe] border-2 border-ink rounded-xl p-3 shadow-[2px_2px_0px_#000] flex items-center gap-2.5">
                  <span className="size-8 rounded-lg bg-white border-2 border-ink flex items-center justify-center shrink-0 shadow-[1px_1px_0px_#000]">
                    <Settings className="size-4 text-ink" />
                  </span>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-ink/75">
                      Analyzed
                    </span>
                    <span className="text-sm sm:text-base font-black text-ink leading-tight">
                      {data.totalRequirements} Total
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Section: 3 Skill Detail Columns */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4 items-start">
            {/* Column 1: Matched Skills */}
            <div className="bg-white border-2 border-ink rounded-2xl p-4 sm:p-5 shadow-[3px_3px_0px_#000] flex flex-col justify-between min-h-[220px]">
              <div>
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2">
                    <span className="size-2.5 rounded-full bg-emerald-500 border border-ink" />
                    <h4 className="font-black text-xs sm:text-sm tracking-wide text-ink uppercase">
                      Matched Skills
                    </h4>
                  </div>
                  <span className="bg-[#d9f99d] border-2 border-ink rounded-md px-2 py-0.5 text-xs font-black text-ink shadow-[1px_1px_0px_#000]">
                    {data.satisfiedCount}
                  </span>
                </div>
                <p className="text-[11px] text-muted font-semibold mb-3">
                  You have the right skills!
                </p>

                {/* Skill List */}
                <div className="flex flex-col gap-2">
                  {visibleMatched.map((skill) => (
                    <div
                      key={skill.id}
                      className="flex items-center gap-2 text-xs sm:text-sm font-bold text-ink"
                    >
                      <CheckCircle2 className="size-4 text-emerald-600 fill-emerald-100 shrink-0" />
                      <span className="truncate">{skill.requiredSkillName}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Show more toggle */}
              {remainingMatchedCount > 0 && (
                <button
                  type="button"
                  onClick={() => setShowAllMatched(!showAllMatched)}
                  className="text-xs text-muted hover:text-ink font-bold cursor-pointer mt-3 text-left transition-colors"
                >
                  {showAllMatched ? "show less" : `+${remainingMatchedCount} more`}
                </button>
              )}
            </div>

            {/* Column 2: Missing Skills */}
            <div className="bg-white border-2 border-ink rounded-2xl p-4 sm:p-5 shadow-[3px_3px_0px_#000] flex flex-col justify-between min-h-[220px]">
              <div>
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2">
                    <span className="size-2.5 rounded-full bg-amber-400 border border-ink" />
                    <h4 className="font-black text-xs sm:text-sm tracking-wide text-ink uppercase">
                      Missing Skills
                    </h4>
                  </div>
                  <span className="bg-[#fef08a] border-2 border-ink rounded-md px-2 py-0.5 text-xs font-black text-ink shadow-[1px_1px_0px_#000]">
                    {data.missingCount}
                  </span>
                </div>
                <p className="text-[11px] text-muted font-semibold mb-3">
                  Important skills not found:
                </p>

                {/* Missing Skill List */}
                <div className="flex flex-col gap-2">
                  {visibleMissing.map((skill) => (
                    <div
                      key={skill.id}
                      className="flex items-center gap-2 text-xs sm:text-sm font-bold text-ink"
                    >
                      <MinusCircle className="size-4 text-amber-500 fill-amber-100 shrink-0" />
                      <span className="truncate">{skill.requiredSkillName}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Show more toggle */}
              {remainingMissingCount > 0 && (
                <button
                  type="button"
                  onClick={() => setShowAllMissing(!showAllMissing)}
                  className="text-xs text-muted hover:text-ink font-bold cursor-pointer mt-3 text-left transition-colors"
                >
                  {showAllMissing ? "show less" : `+${remainingMissingCount} more`}
                </button>
              )}
            </div>

            {/* Column 3: Priority To Improve */}
            <div className="bg-white border-2 border-ink rounded-2xl p-4 sm:p-5 shadow-[3px_3px_0px_#000] flex flex-col justify-between min-h-[220px]">
              <div>
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2">
                    <span className="size-2.5 rounded-full bg-purple-400 border border-ink" />
                    <h4 className="font-black text-xs sm:text-sm tracking-wide text-ink uppercase">
                      Priority to Improve
                    </h4>
                  </div>
                  <span className="bg-[#edddfc] border-2 border-ink rounded-md px-2 py-0.5 text-xs font-black text-ink shadow-[1px_1px_0px_#000]">
                    TOP
                  </span>
                </div>
                <p className="text-[11px] text-muted font-semibold mb-3">
                  Focus on these to boost score:
                </p>

                {/* Ranked Priority List */}
                <div className="flex flex-col gap-2">
                  {visiblePriorities.map((item) => (
                    <div
                      key={item.skillId}
                      className="flex items-center gap-2.5 text-xs sm:text-sm font-bold text-ink"
                    >
                      <span className="size-6 rounded-md bg-[#f5d0fe] border-2 border-ink text-xs font-black text-ink flex items-center justify-center shadow-[1px_1px_0px_#000] shrink-0">
                        {item.priorityRank}
                      </span>
                      <span className="truncate">{item.skillName}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Show more priorities toggle */}
              {hasRemainingPriorities && (
                <button
                  type="button"
                  onClick={() => setShowAllPriorities(!showAllPriorities)}
                  className="text-xs text-muted hover:text-ink font-bold cursor-pointer mt-3 text-left transition-colors"
                >
                  {showAllPriorities ? "less ..." : "more ..."}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer Action Buttons */}
        <div className="border-t-2 sm:border-t-[2.5px] border-ink bg-white/70 px-4 sm:px-7 py-3 sm:py-3.5 flex flex-wrap items-center justify-between gap-2.5 shrink-0">
          {/* Neutral / Not Yet Connected Download Action */}
          <button
            type="button"
            disabled
            title="PDF report download will be available when connected to the C03 report service"
            className="bg-white text-ink/50 border-2 border-ink/40 rounded-xl px-4 py-2.5 text-xs sm:text-sm font-bold flex items-center gap-2 cursor-not-allowed select-none"
          >
            <Download className="size-4" />
            <span>DOWNLOAD REPORT</span>
          </button>

          <div className="flex items-center gap-2.5 ml-auto">

            {/* Close Button */}
            <button
              type="button"
              onClick={onClose}
              className="bg-white hover:bg-gray-100 text-ink border-2 border-ink rounded-xl px-5 py-2.5 shadow-[2px_2px_0px_#000] font-bold text-xs sm:text-sm hover:-translate-y-0.5 active:translate-y-0 transition-all cursor-pointer"
            >
              CLOSE
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
