"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  BarChart3,
  Briefcase,
  ChevronDown,
  Lightbulb,
  Loader2,
  Monitor,
  RefreshCw,
  Zap,
} from "lucide-react";

import { CareerReadinessLoadingModal } from "./CareerReadinessLoadingModal";
import { CareerReadinessResultModal } from "./CareerReadinessResultModal";
import {
  fetchDetailedAnalysisResult,
  formatCareerLevel,
  type DetailedAnalysisResult,
  type TargetRoleOption,
} from "./types";
import { readinessApi } from "@/lib/readinessApi";

interface StartAnalysisPanelProps {
  userId?: string;
  onAnalysisSuccess?: (analysisId: string, result: DetailedAnalysisResult) => void;
}

// Target role selection and analysis trigger panel connected to the C03 Readiness Engine
export function StartAnalysisPanel({ userId, onAnalysisSuccess }: StartAnalysisPanelProps) {
  const [roles, setRoles] = useState<TargetRoleOption[]>([]);
  const [rolesLoading, setRolesLoading] = useState(true);
  const [rolesError, setRolesError] = useState<string | null>(null);

  const [selectedRoleId, setSelectedRoleId] = useState<string>("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const [isLoadingModalOpen, setIsLoadingModalOpen] = useState(false);
  const [isApiDone, setIsApiDone] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<DetailedAnalysisResult | null>(null);
  const [isResultModalOpen, setIsResultModalOpen] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Fetch real target industry profiles from the Readiness Engine on mount
  useEffect(() => {
    let ignore = false;
    readinessApi
      .getIndustryProfiles({ status: "active" })
      .then((profiles) => {
        if (ignore) return;
        const options: TargetRoleOption[] = profiles.map((p) => ({
          id: p.industry_profile_id,
          roleId: p.role_id || p.industry_profile_id,
          label: `${p.role_name} — ${formatCareerLevel(p.career_level)}`,
          roleName: p.role_name,
          careerLevel: formatCareerLevel(p.career_level),
          domainName: p.domain_name || "Information Technology",
        }));
        setRoles(options);
        if (options.length > 0) {
          setSelectedRoleId((prev) => (prev && options.some((o) => o.id === prev) ? prev : options[0].id));
        }
        setRolesLoading(false);
      })
      .catch((err) => {
        if (ignore) return;
        setRolesError(
          err instanceof Error ? err.message : "Failed to load target industry profiles.",
        );
        setRolesLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, []);

  const reloadRoles = async () => {
    setRolesLoading(true);
    setRolesError(null);
    try {
      const profiles = await readinessApi.getIndustryProfiles({ status: "active" });
      const options: TargetRoleOption[] = profiles.map((p) => ({
        id: p.industry_profile_id,
        roleId: p.role_id || p.industry_profile_id,
        label: `${p.role_name} — ${formatCareerLevel(p.career_level)}`,
        roleName: p.role_name,
        careerLevel: formatCareerLevel(p.career_level),
        domainName: p.domain_name || "Information Technology",
      }));
      setRoles(options);
      if (options.length > 0) {
        setSelectedRoleId((prev) => (prev && options.some((o) => o.id === prev) ? prev : options[0].id));
      }
    } catch (err) {
      setRolesError(
        err instanceof Error ? err.message : "Failed to load target industry profiles.",
      );
    } finally {
      setRolesLoading(false);
    }
  };

  const selectedRole = roles.find((r) => r.id === selectedRoleId);

  // Trigger real analysis pipeline using authenticated user ID and selected profile
  const handleStartAnalysis = async () => {
    if (isLoadingModalOpen || !selectedRoleId) {
      return;
    }

    setSubmitError(null);
    setIsApiDone(false);
    setAnalysisResult(null);
    setIsLoadingModalOpen(true);

    try {
      const response = await readinessApi.createAnalysis({
        user_id: userId,
        industry_profile_id: selectedRoleId,
      });

      const analysisId = response.analysisId;
      if (!analysisId) {
        throw new Error("Readiness engine did not return a valid analysis ID.");
      }

      // Fetch full details and deterministic explanation report
      const fullResult = await fetchDetailedAnalysisResult(analysisId);
      setAnalysisResult(fullResult);
      setIsApiDone(true);
    } catch (err) {
      setIsLoadingModalOpen(false);
      setIsApiDone(false);
      setSubmitError(
        err instanceof Error
          ? err.message
          : "Career readiness analysis failed. Please verify backend services and try again.",
      );
    }
  };

  // Transition from animated loader into detailed results modal upon completion
  const handleLoadingComplete = () => {
    setIsLoadingModalOpen(false);
    if (analysisResult) {
      setIsResultModalOpen(true);
      onAnalysisSuccess?.(analysisResult.analysisId, analysisResult);
    }
  };

  return (
    <div className="bg-white border-2 border-ink rounded-2xl p-5 sm:p-6 shadow-[4px_4px_0px_#000]">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="size-5 text-ink" />
        <h2 className="font-extrabold text-lg sm:text-xl text-ink">Start New Analysis</h2>
      </div>

      {/* Submission error message banner */}
      {submitError && (
        <div className="mb-4 bg-red-50 border-2 border-red-500 rounded-xl p-3.5 flex items-start gap-3 shadow-[2px_2px_0px_#ef4444]">
          <AlertCircle className="size-5 text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1 text-xs sm:text-sm font-semibold text-red-800">
            <p className="font-bold">Analysis Failed</p>
            <p className="mt-0.5">{submitError}</p>
          </div>
        </div>
      )}

      {/* Form Controls: Domain & Target Role */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Fixed domain for IT scope */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-ink mb-1.5">
            Domain
          </label>
          <div
            title="Domain is fixed to Information Technology for this evaluation scope"
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

          {rolesLoading ? (
            <div className="w-full bg-white border-2 border-ink rounded-xl px-4 py-3 flex items-center justify-between shadow-[2px_2px_0px_#000]">
              <div className="flex items-center gap-2.5 text-muted text-sm font-semibold">
                <Loader2 className="size-4 animate-spin text-ink" />
                <span>Loading available roles...</span>
              </div>
            </div>
          ) : rolesError ? (
            <div className="w-full bg-red-50 border-2 border-red-400 rounded-xl px-3 py-2 flex items-center justify-between gap-2 shadow-[2px_2px_0px_#ef4444]">
              <span className="text-xs font-bold text-red-700 truncate">{rolesError}</span>
              <button
                type="button"
                onClick={reloadRoles}
                className="text-xs font-black text-ink underline flex items-center gap-1 shrink-0 cursor-pointer"
              >
                <RefreshCw className="size-3" />
                Retry
              </button>
            </div>
          ) : roles.length === 0 ? (
            <div className="w-full bg-gray-50 border-2 border-ink/40 rounded-xl px-4 py-3 text-xs font-semibold text-muted">
              No target roles available.
            </div>
          ) : (
            <>
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
                    {selectedRole ? selectedRole.label : "Select target role"}
                  </span>
                </div>
                <ChevronDown
                  className={`size-5 text-ink shrink-0 transition-transform ${
                    isDropdownOpen ? "rotate-180" : ""
                  }`}
                />
              </button>

              {/* Dropdown Options */}
              {isDropdownOpen && (
                <ul
                  role="listbox"
                  className="absolute left-0 right-0 mt-1.5 bg-white border-2 border-ink rounded-xl shadow-[4px_4px_0px_#000] py-1 z-30 max-h-60 overflow-y-auto"
                >
                  {roles.map((role) => (
                    <li
                      key={role.id}
                      role="option"
                      aria-selected={role.id === selectedRoleId}
                      onClick={() => {
                        setSelectedRoleId(role.id);
                        setIsDropdownOpen(false);
                      }}
                      className={`px-4 py-2.5 text-sm font-semibold cursor-pointer transition-colors flex items-center gap-2.5 ${
                        role.id === selectedRoleId
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
            </>
          )}
        </div>
      </div>

      {/* Full-width Analyze Readiness Button */}
      <button
        type="button"
        disabled={isLoadingModalOpen || rolesLoading || roles.length === 0}
        onClick={handleStartAnalysis}
        className={`mt-4 w-full bg-sun hover:bg-butter border-2 border-ink shadow-[3px_3px_0px_#000] rounded-xl py-3.5 px-6 font-black text-base sm:text-lg text-ink flex items-center justify-center gap-2.5 transition-all ${
          isLoadingModalOpen || rolesLoading || roles.length === 0
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

      {/* Career Readiness Loading Modal with animated progression */}
      <CareerReadinessLoadingModal
        isOpen={isLoadingModalOpen}
        isCompleted={isApiDone}
        onClose={() => setIsLoadingModalOpen(false)}
        onComplete={handleLoadingComplete}
      />

      {/* Career Readiness Results Modal */}
      <CareerReadinessResultModal
        isOpen={isResultModalOpen}
        onClose={() => setIsResultModalOpen(false)}
        data={analysisResult}
      />
    </div>
  );
}
