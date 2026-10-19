"use client";

import { useState } from "react";
import { BarChart3, Briefcase, ChevronDown, Lightbulb, Monitor, Zap } from "lucide-react";

import { CareerReadinessLoadingModal } from "./CareerReadinessLoadingModal";
import { CareerReadinessResultModal } from "./CareerReadinessResultModal";
import {
  DEMO_TARGET_ROLES,
  type DetailedAnalysisResult,
  getAnalysisDetail,
  MOCK_ANALYSIS_DETAILS,
} from "./mockData";

interface StartAnalysisPanelProps {
  userId?: string;
  onStartAnalysis?: (roleId: string) => void;
}

// Start New Analysis panel with domain indicator, role selector, and step instructions
export function StartAnalysisPanel({ onStartAnalysis }: StartAnalysisPanelProps = {}) {
  const [selectedRoleId, setSelectedRoleId] = useState(DEMO_TARGET_ROLES[0].id);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isLoadingModalOpen, setIsLoadingModalOpen] = useState(false);
  const [isResultModalOpen, setIsResultModalOpen] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<DetailedAnalysisResult | null>(null);

  const selectedRole =
    DEMO_TARGET_ROLES.find((r) => r.id === selectedRoleId) || DEMO_TARGET_ROLES[0];

  const handleStartAnalysis = () => {
    // Prevent duplicate analysis submissions while the loading sequence is running
    if (isLoadingModalOpen) {
      return;
    }

    onStartAnalysis?.(selectedRoleId);
    setIsLoadingModalOpen(true);
  };

  // Called when all 6 steps finish to transition into the results modal
  const handleLoadingComplete = () => {
    setIsLoadingModalOpen(false);

    // Retrieve or dynamically generate the illustrative detailed result for the chosen role
    const matchedRecord =
      selectedRoleId === "software-testing"
        ? MOCK_ANALYSIS_DETAILS["hist-1"]
        : selectedRoleId === "web-developer"
          ? MOCK_ANALYSIS_DETAILS["hist-2"]
          : selectedRoleId === "data-analyst"
            ? MOCK_ANALYSIS_DETAILS["hist-3"]
            : getAnalysisDetail({
                id: `analysis-${Date.now()}`,
                role: selectedRole.label.split("—")[0].trim(),
                careerLevel: selectedRole.label.split("—")[1]?.trim() || "Junior",
                readinessScore: 78,
                date: "Just now",
              });

    setAnalysisResult(matchedRecord);
    setIsResultModalOpen(true);
  };

  return (
    <div className="bg-white border-2 border-ink rounded-2xl p-5 sm:p-6 shadow-[4px_4px_0px_#000]">
      {/* Card Header with doodle sparks */}
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="size-5 text-ink" />
        <h2 className="font-extrabold text-lg sm:text-xl text-ink">Start New Analysis</h2>
      </div>

      {/* Form Controls: Domain & Target Role */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Fixed, non-selectable domain for PP1 demonstration */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-ink mb-1.5">
            Domain
          </label>
          <div
            title="Domain is fixed for this demonstration"
            className="w-full bg-[#f1f4f9] border-2 border-ink/30 rounded-xl px-4 py-3 flex items-center gap-3 cursor-not-allowed select-none"
          >
            <Monitor className="size-5 text-ink/50 shrink-0" />
            <span className="text-sm font-semibold text-ink/70">
              Information Technology — IT
            </span>
          </div>
        </div>

        {/* Target role dropdown selector */}
        <div className="relative">
          <label className="block text-xs font-bold uppercase tracking-wider text-ink mb-1.5">
            Target Role
          </label>
          <button
            type="button"
            onClick={() => setIsDropdownOpen((prev) => !prev)}
            aria-expanded={isDropdownOpen}
            aria-haspopup="listbox"
            className="w-full bg-white border-2 border-ink rounded-xl px-4 py-3 flex items-center justify-between gap-2 shadow-[2px_2px_0px_#000] hover:bg-cream transition-colors text-left cursor-pointer"
          >
            <div className="flex items-center gap-3 min-w-0">
              <Briefcase className="size-5 text-ink shrink-0" />
              <span className="text-sm font-bold text-ink truncate">
                {selectedRole.label}
              </span>
            </div>
            <ChevronDown
              className={`size-5 text-ink shrink-0 transition-transform ${isDropdownOpen ? "rotate-180" : ""
                }`}
            />
          </button>

          {/* Dropdown Options */}
          {isDropdownOpen && (
            <ul
              role="listbox"
              className="absolute left-0 right-0 mt-1.5 bg-white border-2 border-ink rounded-xl shadow-[4px_4px_0px_#000] py-1 z-30 overflow-hidden"
            >
              {DEMO_TARGET_ROLES.map((role) => (
                <li
                  key={role.id}
                  role="option"
                  aria-selected={role.id === selectedRoleId}
                  onClick={() => {
                    setSelectedRoleId(role.id);
                    setIsDropdownOpen(false);
                  }}
                  className={`px-4 py-2.5 text-sm font-semibold cursor-pointer transition-colors flex items-center gap-2.5 ${role.id === selectedRoleId
                      ? "bg-lime text-ink font-bold"
                      : "hover:bg-sand text-ink"
                    }`}
                >
                  <Briefcase className="size-4 shrink-0" />
                  <span>{role.label}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Full-width Analyze Readiness Button */}
      <button
        type="button"
        disabled={isLoadingModalOpen}
        onClick={handleStartAnalysis}
        className={`mt-4 w-full bg-sun hover:bg-butter border-2 border-ink shadow-[3px_3px_0px_#000] rounded-xl py-3.5 px-6 font-black text-base sm:text-lg text-ink flex items-center justify-center gap-2.5 transition-all ${
          isLoadingModalOpen
            ? "opacity-60 cursor-not-allowed"
            : "cursor-pointer hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_#000] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none"
        }`}
      >
        <Zap className={`size-5 fill-ink text-ink ${isLoadingModalOpen ? "animate-pulse" : ""}`} />
        <span>{isLoadingModalOpen ? "Analyzing Readiness..." : "Analyze Readiness"}</span>
      </button>

      {/* Instructions Panel */}
      <div className="mt-5 bg-lime border-2 border-ink rounded-xl p-5 sm:p-6 relative overflow-hidden shadow-[2px_2px_0px_#000]">
        <div className="flex items-center gap-2.5 mb-4">
          <span className="size-8 rounded-full bg-white border-2 border-ink flex items-center justify-center shadow-[1px_1px_0px_#000] shrink-0">
            <Lightbulb className="size-4 text-ink fill-sun" />
          </span>
          <h3 className="font-extrabold text-base sm:text-lg text-ink">
            What happens next?
          </h3>
        </div>

        {/* 3 Step List */}
        <div className="flex flex-col gap-3.5 w-full">
          <div className="flex items-start gap-3">
            <span className="size-7 rounded-full bg-[#edddfc] border-2 border-ink font-black text-xs flex items-center justify-center shadow-[1px_1px_0px_#000] shrink-0 mt-0.5">
              1
            </span>
            <div>
              <p className="font-bold text-xs sm:text-sm text-ink leading-tight">
                We compare your saved skill profile
              </p>
              <p className="text-[11px] sm:text-xs text-ink/80 mt-0.5 leading-relaxed">
                Your demonstrated skills and proficiency are compared with the selected industry role.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <span className="size-7 rounded-full bg-[#edddfc] border-2 border-ink font-black text-xs flex items-center justify-center shadow-[1px_1px_0px_#000] shrink-0 mt-0.5">
              2
            </span>
            <div>
              <p className="font-bold text-xs sm:text-sm text-ink leading-tight">
                We evaluate skill matches
              </p>
              <p className="text-[11px] sm:text-xs text-ink/80 mt-0.5 leading-relaxed">
                Both exact matches and verified relationship-based skill matches are considered.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <span className="size-7 rounded-full bg-[#edddfc] border-2 border-ink font-black text-xs flex items-center justify-center shadow-[1px_1px_0px_#000] shrink-0 mt-0.5">
              3
            </span>
            <div>
              <p className="font-bold text-xs sm:text-sm text-ink leading-tight">
                We identify your readiness and gaps
              </p>
              <p className="text-[11px] sm:text-xs text-ink/80 mt-0.5 leading-relaxed">
                You&apos;ll receive a readiness score, skill gaps, and ranked learning priorities for improvement.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Career Readiness Loading Modal with 6-step progression */}
      <CareerReadinessLoadingModal
        isOpen={isLoadingModalOpen}
        onClose={() => setIsLoadingModalOpen(false)}
        onComplete={handleLoadingComplete}
      />

      {/* Career Readiness Results Modal shown after completion */}
      <CareerReadinessResultModal
        isOpen={isResultModalOpen}
        onClose={() => setIsResultModalOpen(false)}
        data={analysisResult}
      />
    </div>
  );
}
