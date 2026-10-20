"use client";

import { useState, useEffect } from "react";
import type {
  CandidateRelationshipItem,
  SkillRelationshipType,
} from "@/lib/ssksApi";
import { reviewCandidateRelationship } from "@/lib/ssksApi";
import {
  CheckCircle2,
  XCircle,
  ArrowRight,
  ArrowLeftRight,
  AlertCircle,
  Loader2,
  ShieldCheck,
  Info,
} from "lucide-react";

export interface CandidateRefineModalProps {
  isOpen: boolean;
  candidate: CandidateRelationshipItem | null;
  initialMode?: "REFINE_AND_VERIFY" | "REJECT";
  skillsMap: Map<string, string>;
  reviewerId?: string;
  onClose: () => void;
  onSuccess: (updated: CandidateRelationshipItem, action: "APPROVE" | "REJECT") => void;
}

export const SUPPORTED_RELATIONSHIP_TYPES: SkillRelationshipType[] = [
  "EQUIVALENT_TO",
  "BROADER_THAN",
  "NARROWER_THAN",
  "PART_OF",
  "PREREQUISITE_OF",
  "RELATED_TO",
];

// Semantic descriptions for SSKS relationship types
export const RELATIONSHIP_DESCRIPTIONS: Record<SkillRelationshipType, string> = {
  EQUIVALENT_TO:
    "Source and target skills are exact synonyms, alternative brandings, or functionally identical.",
  BROADER_THAN:
    "Source skill is a broader, superset domain or generalization of the target skill.",
  NARROWER_THAN:
    "Source skill is a specialized sub-discipline or narrow specialization of the target skill.",
  PART_OF:
    "Source skill is an integral library, module, or technology component forming the target (e.g., React → PART_OF → MERN Stack).",
  PREREQUISITE_OF:
    "Source skill is foundational knowledge or an essential prerequisite before mastering the target skill.",
  RELATED_TO:
    "Skills share technical ecosystem or complementary usage without strict hierarchical dependency.",
};

// Generates readable English sentence preview for directional verification
export function getRelationshipSentence(
  sourceName: string,
  relType: SkillRelationshipType,
  targetName: string,
): string {
  switch (relType) {
    case "EQUIVALENT_TO":
      return `"${sourceName}" is functionally equivalent to or synonymous with "${targetName}".`;
    case "BROADER_THAN":
      return `"${sourceName}" is a broader concept that encompasses "${targetName}".`;
    case "NARROWER_THAN":
      return `"${sourceName}" is a specialized subfield or narrower concept within "${targetName}".`;
    case "PART_OF":
      return `"${sourceName}" is an integral component or constituent part of "${targetName}".`;
    case "PREREQUISITE_OF":
      return `"${sourceName}" is foundational knowledge required before learning "${targetName}".`;
    case "RELATED_TO":
      return `"${sourceName}" shares complementary domain context with "${targetName}".`;
    default:
      return `"${sourceName}" → ${relType} → "${targetName}"`;
  }
}

// Background badge colors aligned with Shared Knowledge taxonomy view
export function getRelationshipBadgeColor(type: string): string {
  switch (type) {
    case "EQUIVALENT_TO":
      return "bg-[#7df9ff]";
    case "BROADER_THAN":
    case "NARROWER_THAN":
      return "bg-[#d0ffa4]";
    case "PREREQUISITE_OF":
      return "bg-[#ffde4d]";
    case "PART_OF":
      return "bg-[#edddfc]";
    default:
      return "bg-[#ffefdc]";
  }
}

// Human-readable labels for SSKS relationship types
export function formatRelationshipType(type: string): string {
  const map: Record<string, string> = {
    EQUIVALENT_TO: "Equivalent To",
    BROADER_THAN: "Broader Than",
    NARROWER_THAN: "Narrower Than",
    PART_OF: "Part Of",
    PREREQUISITE_OF: "Prerequisite Of",
    RELATED_TO: "Related To",
  };
  return map[type] || type.replace(/_/g, " ");
}

// Validates HTTP/HTTPS URL format
function isValidUrl(url: string): boolean {
  if (!url || !url.trim()) return true;
  try {
    const parsed = new URL(url.trim());
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function CandidateRefineModal({
  isOpen,
  candidate,
  initialMode = "REFINE_AND_VERIFY",
  skillsMap,
  reviewerId = "admin-reviewer",
  onClose,
  onSuccess,
}: CandidateRefineModalProps) {
  const [currentMode, setCurrentMode] = useState<"REFINE_AND_VERIFY" | "REJECT">(initialMode);
  const [sourceSkillId, setSourceSkillId] = useState("");
  const [targetSkillId, setTargetSkillId] = useState("");
  const [relationshipType, setRelationshipType] = useState<SkillRelationshipType>("RELATED_TO");
  const [evidenceDescription, setEvidenceDescription] = useState("");
  const [evidenceUrl, setEvidenceUrl] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [urlError, setUrlError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize form fields whenever modal opens or candidate changes
  useEffect(() => {
    if (candidate) {
      setCurrentMode(initialMode);
      setSourceSkillId(candidate.source_skill_id);
      setTargetSkillId(candidate.target_skill_id);
      setRelationshipType(candidate.proposed_relationship_type);
      setEvidenceDescription(candidate.evidence_description || "");
      setEvidenceUrl(candidate.evidence_url || "");
      setReviewNote(
        candidate.review_note ||
          (initialMode === "REFINE_AND_VERIFY"
            ? "Verified and approved by administrator"
            : "Rejected during taxonomy candidate review"),
      );
      setUrlError(null);
      setSubmitError(null);
      setIsSubmitting(false);
    }
  }, [candidate, initialMode, isOpen]);

  if (!isOpen || !candidate) {
    return null;
  }

  // Swap relationship direction (exchanges source and target skills)
  const handleSwapDirection = () => {
    const temp = sourceSkillId;
    setSourceSkillId(targetSkillId);
    setTargetSkillId(temp);
    setSubmitError(null);
  };

  // Handle URL change with inline format validation
  const handleUrlChange = (value: string) => {
    setEvidenceUrl(value);
    const clean = value.trim();
    if (clean && !isValidUrl(clean)) {
      setUrlError("URL must start with http:// or https:// and be a valid web address.");
    } else {
      setUrlError(null);
    }
    setSubmitError(null);
  };

  // Submit Refined Approval & Publish
  const handleSubmitApproval = async () => {
    if (evidenceUrl.trim() && !isValidUrl(evidenceUrl)) {
      setUrlError("URL must start with http:// or https:// and be a valid web address.");
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const updated = await reviewCandidateRelationship(
        candidate.candidate_relationship_id,
        {
          action: "APPROVE",
          source_skill_id: sourceSkillId,
          target_skill_id: targetSkillId,
          relationship_type: relationshipType,
          evidence_description: evidenceDescription.trim() || undefined,
          evidence_url: evidenceUrl.trim() || undefined,
          review_note: reviewNote.trim() || undefined,
        },
        reviewerId,
      );

      onSuccess(updated, "APPROVE");
      onClose();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to verify and publish candidate relationship";
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Rejection
  const handleSubmitRejection = async () => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const updated = await reviewCandidateRelationship(
        candidate.candidate_relationship_id,
        {
          action: "REJECT",
          review_note: reviewNote.trim() || undefined,
        },
        reviewerId,
      );

      onSuccess(updated, "REJECT");
      onClose();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to reject candidate relationship";
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto">
      {/* MODE 1: REFINE & VERIFY WORKBENCH */}
      {currentMode === "REFINE_AND_VERIFY" ? (
        <div className="hard-shadow w-full max-w-2xl rounded-xl border-2 border-ink bg-white p-6 my-8 max-h-[90vh] flex flex-col">
          {/* Modal Header */}
          <div className="flex items-start justify-between gap-4 border-b-2 border-ink/10 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <div className="flex size-8 items-center justify-center rounded-lg border-2 border-ink bg-[#7df9ff] hard-shadow-sm">
                  <ShieldCheck className="size-5 text-ink" />
                </div>
                <div>
                  <h2 className="text-lg font-black text-ink">
                    Refine &amp; Verify Workbench
                  </h2>
                  <p className="text-xs text-muted">
                    Verify candidate relationship, adjust direction and ontology type, record evidence, and publish.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col items-end gap-1">
              <span className="font-mono text-xs font-black text-ink">
                {candidate.candidate_relationship_id}
              </span>
              {candidate.confidence_score !== null && (
                <span className="hard-shadow-sm rounded bg-[#fff9f2] border border-ink px-2 py-0.5 text-[10px] font-bold text-ink">
                  Confidence: {Math.round(candidate.confidence_score * 100)}%
                </span>
              )}
            </div>
          </div>

          {/* Scrollable Form Body */}
          <div className="flex-1 overflow-y-auto py-4 space-y-5 pr-1">
            {/* Inline Error Alert */}
            {submitError && (
              <div className="rounded-lg border-2 border-ink bg-[#ffbaba] p-3 text-xs font-bold text-ink flex items-start gap-2">
                <AlertCircle className="size-4 text-ink shrink-0 mt-0.5" />
                <div className="flex-1">
                  <span className="font-black">Submission Error:</span> {submitError}
                </div>
              </div>
            )}

            {/* 1. Skill Hierarchy & Direction Control */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-black uppercase tracking-wider text-ink">
                  Skill Relationship Direction
                </label>
                <button
                  type="button"
                  onClick={handleSwapDirection}
                  disabled={isSubmitting}
                  className="hard-shadow-sm inline-flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#7df9ff] px-2.5 py-1 text-xs font-black text-ink hover:bg-[#5ce1e6] active:translate-y-0.5 transition-all cursor-pointer disabled:opacity-50"
                  title="Swap relationship source and target"
                >
                  <ArrowLeftRight className="size-3.5" />
                  <span>Swap direction</span>
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
                {/* Source Skill Card */}
                <div className="rounded-lg border-2 border-ink bg-[#fff9f2] p-3 hard-shadow-sm">
                  <span className="text-[10px] font-black uppercase text-muted block">
                    Source Skill (Subject)
                  </span>
                  <span className="text-sm font-black text-ink block truncate mt-0.5">
                    {skillsMap.get(sourceSkillId) || `Unknown (${sourceSkillId})`}
                  </span>
                  <span className="font-mono text-[11px] font-bold text-muted block mt-0.5">
                    {sourceSkillId}
                  </span>
                </div>

                {/* Target Skill Card */}
                <div className="rounded-lg border-2 border-ink bg-[#fff9f2] p-3 hard-shadow-sm">
                  <span className="text-[10px] font-black uppercase text-muted block">
                    Target Skill (Object)
                  </span>
                  <span className="text-sm font-black text-ink block truncate mt-0.5">
                    {skillsMap.get(targetSkillId) || `Unknown (${targetSkillId})`}
                  </span>
                  <span className="font-mono text-[11px] font-bold text-muted block mt-0.5">
                    {targetSkillId}
                  </span>
                </div>
              </div>
            </div>

            {/* 2. Relationship Type Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-black uppercase tracking-wider text-ink block">
                Ontology Relationship Type
              </label>
              <select
                value={relationshipType}
                onChange={(e) => {
                  setRelationshipType(e.target.value as SkillRelationshipType);
                  setSubmitError(null);
                }}
                disabled={isSubmitting}
                className="hard-shadow-sm w-full rounded-lg border-2 border-ink bg-white px-3 py-2 text-xs font-black text-ink focus:outline-none cursor-pointer"
              >
                {SUPPORTED_RELATIONSHIP_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {formatRelationshipType(type)} ({type})
                  </option>
                ))}
              </select>

              {/* Type Description Helper */}
              <div className="flex items-start gap-1.5 rounded-md border border-ink/30 bg-[#ffefdc] p-2 text-xs text-ink/90">
                <Info className="size-3.5 text-ink shrink-0 mt-0.5" />
                <span>
                  <strong className="text-ink">Semantics:</strong>{" "}
                  {RELATIONSHIP_DESCRIPTIONS[relationshipType]}
                </span>
              </div>
            </div>

            {/* 3. Live Directional Preview */}
            <div className="space-y-1.5">
              <label className="text-xs font-black uppercase tracking-wider text-ink block">
                Live Verification Preview
              </label>
              <div className="rounded-lg border-2 border-ink bg-[#fff9f2] p-3.5 hard-shadow-sm space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="min-w-0">
                    <span className="text-xs font-black text-ink block truncate">
                      {skillsMap.get(sourceSkillId) || sourceSkillId}
                    </span>
                    <span className="font-mono text-[10px] text-muted">{sourceSkillId}</span>
                  </div>

                  <span
                    className={`hard-shadow-sm shrink-0 flex items-center gap-1.5 rounded-lg border-2 border-ink px-3 py-1 text-xs font-black uppercase text-ink ${getRelationshipBadgeColor(
                      relationshipType,
                    )}`}
                  >
                    <span>{formatRelationshipType(relationshipType)}</span>
                    <ArrowRight className="size-3 stroke-[2.5]" />
                  </span>

                  <div className="min-w-0 text-right">
                    <span className="text-xs font-black text-ink block truncate">
                      {skillsMap.get(targetSkillId) || targetSkillId}
                    </span>
                    <span className="font-mono text-[10px] text-muted">{targetSkillId}</span>
                  </div>
                </div>

                {/* Plain English Directional Sentence */}
                <div className="border-t border-ink/10 pt-2 text-xs font-bold text-ink/80 italic">
                  &ldquo;
                  {getRelationshipSentence(
                    skillsMap.get(sourceSkillId) || sourceSkillId,
                    relationshipType,
                    skillsMap.get(targetSkillId) || targetSkillId,
                  )}
                  &rdquo;
                </div>
              </div>
            </div>

            {/* 4. Evidence Description (Justification) */}
            <div className="space-y-1">
              <label className="text-xs font-black text-ink flex items-center justify-between">
                <span>Evidence Description / Justification</span>
                <span className="text-[10px] font-bold text-muted">Authoritative Proof</span>
              </label>
              <textarea
                value={evidenceDescription}
                onChange={(e) => {
                  setEvidenceDescription(e.target.value);
                  setSubmitError(null);
                }}
                placeholder="e.g. Reviewed against authoritative documentation describing the components of the MERN stack."
                rows={2}
                disabled={isSubmitting}
                className="hard-shadow-sm w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2.5 text-xs text-ink placeholder:text-muted focus:outline-none"
              />
            </div>

            {/* 5. Evidence URL (Optional with format validation) */}
            <div className="space-y-1">
              <label className="text-xs font-black text-ink flex items-center justify-between">
                <span>Supporting Documentation URL (Optional)</span>
                <span className="text-[10px] font-bold text-muted">http:// or https://</span>
              </label>
              <input
                type="url"
                value={evidenceUrl}
                onChange={(e) => handleUrlChange(e.target.value)}
                placeholder="https://react.dev/learn or official documentation reference"
                disabled={isSubmitting}
                className={`hard-shadow-sm w-full rounded-lg border-2 p-2.5 text-xs text-ink placeholder:text-muted focus:outline-none ${
                  urlError ? "border-red-600 bg-red-50" : "border-ink bg-[#fff9f2]"
                }`}
              />
              {urlError && (
                <p className="text-[11px] font-bold text-red-600 mt-0.5">
                  {urlError}
                </p>
              )}
            </div>

            {/* 6. Administrative Review Note */}
            <div className="space-y-1">
              <label className="text-xs font-black text-ink flex items-center justify-between">
                <span>Administrative Audit Note</span>
                <span className="text-[10px] font-bold text-muted">Review Log</span>
              </label>
              <textarea
                value={reviewNote}
                onChange={(e) => {
                  setReviewNote(e.target.value);
                  setSubmitError(null);
                }}
                placeholder="e.g. Relationship type and direction verified during admin workbench review."
                rows={2}
                disabled={isSubmitting}
                className="hard-shadow-sm w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2.5 text-xs text-ink placeholder:text-muted focus:outline-none"
              />
            </div>
          </div>

          {/* Modal Actions Footer */}
          <div className="border-t-2 border-ink/10 pt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => setCurrentMode("REJECT")}
              disabled={isSubmitting}
              className="hard-shadow-sm w-full sm:w-auto rounded-lg border-2 border-ink bg-[#ffbaba] px-3.5 py-2 text-xs font-black text-ink hover:bg-[#fa9c9c] disabled:opacity-50 cursor-pointer"
            >
              Reject Candidate Instead
            </button>

            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="hard-shadow-sm rounded-lg border-2 border-ink bg-white px-4 py-2 text-xs font-bold text-ink hover:bg-[#fff9f2] disabled:opacity-50 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmitApproval}
                disabled={isSubmitting || !!urlError}
                className="hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#d0ffa4] px-4 py-2 text-xs font-black text-ink hover:bg-[#b8f582] active:translate-y-0.5 transition-all disabled:opacity-50 cursor-pointer"
              >
                {isSubmitting ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <CheckCircle2 className="size-3.5" />
                )}
                Approve &amp; Publish
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* MODE 2: REJECT CONFIRMATION MODAL */
        <div className="hard-shadow w-full max-w-md rounded-xl border-2 border-ink bg-white p-6">
          <div className="flex items-center gap-2">
            <div className="flex size-8 items-center justify-center rounded-lg border-2 border-ink bg-[#ffbaba] hard-shadow-sm">
              <XCircle className="size-5 text-ink" />
            </div>
            <div>
              <h3 className="text-base font-black text-ink">
                Reject Candidate Relationship
              </h3>
              <span className="font-mono text-xs text-muted">
                {candidate.candidate_relationship_id}
              </span>
            </div>
          </div>

          {/* Inline Error alert inside modal */}
          {submitError && (
            <div className="mt-3 rounded-lg border-2 border-ink bg-[#ffbaba] p-2.5 text-xs font-bold text-ink">
              {submitError}
            </div>
          )}

          {/* Candidate relationship preview */}
          <div className="mt-3 p-3 rounded-lg border-2 border-ink bg-[#fff9f2] hard-shadow-sm flex items-center justify-between gap-2">
            <div className="min-w-0">
              <span className="text-xs font-black text-ink block truncate">
                {skillsMap.get(candidate.source_skill_id) || candidate.source_skill_id}
              </span>
              <span className="font-mono text-[10px] text-muted">
                {candidate.source_skill_id}
              </span>
            </div>
            <span
              className={`hard-shadow-sm shrink-0 flex items-center gap-1 rounded border border-ink px-2 py-0.5 text-[10px] font-black uppercase text-ink ${getRelationshipBadgeColor(
                candidate.proposed_relationship_type,
              )}`}
            >
              {formatRelationshipType(candidate.proposed_relationship_type)}
              <ArrowRight className="size-3" />
            </span>
            <div className="min-w-0 text-right">
              <span className="text-xs font-black text-ink block truncate">
                {skillsMap.get(candidate.target_skill_id) || candidate.target_skill_id}
              </span>
              <span className="font-mono text-[10px] text-muted">
                {candidate.target_skill_id}
              </span>
            </div>
          </div>

          <p className="mt-3 text-xs text-muted">
            Rejecting will mark this candidate as rejected and discard it from canonical ontology inclusion. No canonical relationship will be published.
          </p>

          <div className="mt-4">
            <label className="block text-xs font-bold text-ink">Rejection Audit Note</label>
            <textarea
              value={reviewNote}
              onChange={(e) => {
                setReviewNote(e.target.value);
                setSubmitError(null);
              }}
              placeholder="Reason for rejecting this candidate relationship..."
              rows={3}
              disabled={isSubmitting}
              className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2.5 text-xs text-ink placeholder:text-muted focus:outline-none"
            />
          </div>

          <div className="mt-5 flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={() => setCurrentMode("REFINE_AND_VERIFY")}
              disabled={isSubmitting}
              className="text-xs font-bold text-muted underline hover:text-ink cursor-pointer"
            >
              Back to Refine
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="hard-shadow-sm rounded-lg border-2 border-ink bg-white px-4 py-2 text-xs font-bold text-ink hover:bg-[#fff9f2] cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmitRejection}
                disabled={isSubmitting}
                className="hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#ffbaba] px-4 py-2 text-xs font-black text-ink hover:bg-[#fa9c9c] cursor-pointer"
              >
                {isSubmitting ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <XCircle className="size-3.5" />
                )}
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
