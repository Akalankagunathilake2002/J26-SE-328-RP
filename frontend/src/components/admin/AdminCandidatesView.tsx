"use client";

import { useState, useMemo, useEffect } from "react";
import type { CandidateRelationshipItem, SkillItem, SnapshotMetadataItem, } from "@/lib/ssksApi";
import { fetchSsksCandidateRelationships, fetchSsksSkillsAll, fetchSsksSnapshotMetadata, } from "@/lib/ssksApi";
import { Clock, CheckCircle2, XCircle, ArrowRight, AlertCircle, Loader2, Filter, Search, RotateCcw, Sparkles, ChevronLeft, ChevronRight, ShieldCheck, ExternalLink, } from "lucide-react";
import {
  CandidateRefineModal, formatRelationshipType, getRelationshipBadgeColor,
} from "./CandidateRefineModal";

export { formatRelationshipType, getRelationshipBadgeColor };

interface AdminCandidatesViewProps {
  initialCandidates: CandidateRelationshipItem[];
  initialSkills?: SkillItem[];
  reviewerId?: string;
}

type CandidateTab = "RELATIONSHIPS" | "ENTITIES";

const ITEMS_PER_PAGE = 10;

// In-memory module cache to avoid refetching skill catalogue repeatedly
let cachedSkillsCatalogue: Map<string, string> | null = null;

// Renders skill card displaying preferred_name prominently with canonical ID underneath
function renderSkillBadge(skillId: string, skillsMap: Map<string, string>, isLoading: boolean) {
  const hasSkill = skillsMap.has(skillId);
  const skillName = hasSkill ? skillsMap.get(skillId)! : `Unknown skill (${skillId})`;

  return (
    <div className="hard-shadow-sm flex flex-col justify-center rounded-lg border-2 border-ink bg-[#fff9f2] px-3.5 py-1.5 min-w-[140px] sm:min-w-[170px] max-w-[280px]">
      <div className="flex items-center gap-1.5">
        {isLoading && !hasSkill ? (
          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-muted animate-pulse">
            <Loader2 className="size-3 animate-spin text-ink" />
            <span>Loading skill...</span>
          </span>
        ) : (
          <span
            className={`text-xs sm:text-sm font-black truncate text-ink ${!hasSkill ? "italic text-ink/75" : ""
              }`}
            title={skillName}
          >
            {skillName}
          </span>
        )}
      </div>
      <span className="font-mono text-[10px] sm:text-[11px] font-bold text-muted mt-0.5 tracking-tight">
        {skillId}
      </span>
    </div>
  );
}

export function AdminCandidatesView({
  initialCandidates,
  initialSkills,
  reviewerId = "admin-reviewer",
}: AdminCandidatesViewProps) {
  const [activeTab, setActiveTab] = useState<CandidateTab>("RELATIONSHIPS");
  const [candidates, setCandidates] = useState<CandidateRelationshipItem[]>(initialCandidates);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Active candidate and mode for Refine & Verify modal
  const [activeCandidate, setActiveCandidate] = useState<CandidateRelationshipItem | null>(null);
  const [modalMode, setModalMode] = useState<"REFINE_AND_VERIFY" | "REJECT">("REFINE_AND_VERIFY");

  // Notification toast state
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  // Snapshot metadata state
  const [snapshotMeta, setSnapshotMeta] = useState<SnapshotMetadataItem | null>(null);

  // Skill lookup map and fetch states
  const [skillsMap, setSkillsMap] = useState<Map<string, string>>(() => {
    if (initialSkills && initialSkills.length > 0) {
      const map = new Map(initialSkills.map((s) => [s.skill_id, s.preferred_name]));
      cachedSkillsCatalogue = map;
      return map;
    }
    return cachedSkillsCatalogue || new Map();
  });
  const [isSkillsLoading, setIsSkillsLoading] = useState<boolean>(() => {
    if (initialSkills && initialSkills.length > 0) return false;
    return !cachedSkillsCatalogue || cachedSkillsCatalogue.size === 0;
  });
  const [skillsError, setSkillsError] = useState<string | null>(null);

  // Retrieve canonical skills and snapshot metadata on mount
  useEffect(() => {
    let isMounted = true;

    if (skillsMap.size === 0) {
      fetchSsksSkillsAll()
        .then((skills) => {
          if (isMounted) {
            const map = new Map(skills.map((s) => [s.skill_id, s.preferred_name]));
            cachedSkillsCatalogue = map;
            setSkillsMap(map);
            setIsSkillsLoading(false);
          }
        })
        .catch((err: unknown) => {
          if (isMounted) {
            const msg = err instanceof Error ? err.message : "Failed to load canonical skills";
            setSkillsError(msg);
            setIsSkillsLoading(false);
          }
        });
    }

    fetchSsksSnapshotMetadata("SkillGap")
      .then((meta) => {
        if (isMounted) {
          setSnapshotMeta(meta);
        }
      })
      .catch(() => { });

    return () => {
      isMounted = false;
    };
  }, [skillsMap.size]);

  const pendingCount = useMemo(() => {
    return candidates.filter((c) => c.review_status === "PENDING").length;
  }, [candidates]);

  // Refresh candidate relationships, skills, and snapshot metadata from API
  const handleRefresh = async () => {
    setIsRefreshing(true);
    setNotification(null);
    try {
      const [candsResult, skillsResult, metaResult] = await Promise.allSettled([
        fetchSsksCandidateRelationships({ limit: 500 }),
        fetchSsksSkillsAll(),
        fetchSsksSnapshotMetadata("SkillGap"),
      ]);

      if (candsResult.status === "fulfilled") {
        setCandidates(candsResult.value);
      } else {
        const msg =
          candsResult.reason instanceof Error
            ? candsResult.reason.message
            : "Failed to refresh candidates";
        setNotification({ type: "error", message: msg });
      }

      if (skillsResult.status === "fulfilled") {
        const map = new Map(skillsResult.value.map((s) => [s.skill_id, s.preferred_name]));
        cachedSkillsCatalogue = map;
        setSkillsMap(map);
        setSkillsError(null);
      } else {
        const msg =
          skillsResult.reason instanceof Error
            ? skillsResult.reason.message
            : "Failed to refresh canonical skills";
        setSkillsError(msg);
      }

      if (metaResult.status === "fulfilled") {
        setSnapshotMeta(metaResult.value);
      }
    } finally {
      setIsRefreshing(false);
    }
  };

  const filteredCandidates = useMemo(() => {
    return candidates.filter((item) => {
      const matchesStatus =
        statusFilter === "ALL" ? true : item.review_status === statusFilter;

      const q = searchTerm.toLowerCase().trim();
      const sourceName = (skillsMap.get(item.source_skill_id) || "").toLowerCase();
      const targetName = (skillsMap.get(item.target_skill_id) || "").toLowerCase();

      const matchesSearch =
        !q ||
        sourceName.includes(q) ||
        targetName.includes(q) ||
        item.source_skill_id.toLowerCase().includes(q) ||
        item.target_skill_id.toLowerCase().includes(q) ||
        item.proposed_relationship_type.toLowerCase().includes(q) ||
        item.candidate_relationship_id.toLowerCase().includes(q) ||
        (item.review_note && item.review_note.toLowerCase().includes(q)) ||
        (item.evidence_description && item.evidence_description.toLowerCase().includes(q));

      return matchesStatus && matchesSearch;
    });
  }, [candidates, statusFilter, searchTerm, skillsMap]);

  // Pagination
  const totalPages = Math.ceil(filteredCandidates.length / ITEMS_PER_PAGE) || 1;
  const paginatedCandidates = useMemo(() => {
    const start = (page - 1) * ITEMS_PER_PAGE;
    return filteredCandidates.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredCandidates, page]);

  // Open Refine & Verify Workbench modal
  const handleOpenWorkbench = (
    candidate: CandidateRelationshipItem,
    mode: "REFINE_AND_VERIFY" | "REJECT" = "REFINE_AND_VERIFY",
  ) => {
    setActiveCandidate(candidate);
    setModalMode(mode);
  };

  // Handle successful approval or rejection from modal
  const handleModalSuccess = (
    updated: CandidateRelationshipItem,
    action: "APPROVE" | "REJECT",
  ) => {
    setCandidates((prev) =>
      prev.map((c) =>
        c.candidate_relationship_id === updated.candidate_relationship_id ? updated : c,
      ),
    );

    if (action === "APPROVE") {
      fetchSsksSnapshotMetadata("SkillGap")
        .then((m) => setSnapshotMeta(m))
        .catch(() => { });
    }

    const versionMsg =
      action === "APPROVE" && updated.published_snapshot_version
        ? ` (Snapshot: ${updated.published_snapshot_version})`
        : "";

    setNotification({
      type: "success",
      message:
        action === "APPROVE"
          ? `Candidate ${updated.candidate_relationship_id} was successfully verified, promoted to canonical, and published into active knowledge${versionMsg}.`
          : `Candidate relationship ${updated.candidate_relationship_id} was rejected.`,
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full border border-ink bg-[#d0ffa4] px-2.5 py-0.5 text-xs font-black uppercase text-ink">
            <CheckCircle2 className="size-3.5" />
            Approved &amp; Verified
          </span>
        );
      case "REJECTED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full border border-ink bg-[#ffbaba] px-2.5 py-0.5 text-xs font-black uppercase text-ink">
            <XCircle className="size-3.5" />
            Rejected
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full border border-ink bg-[#ffde4d] px-2.5 py-0.5 text-xs font-black uppercase text-ink">
            <Clock className="size-3.5" />
            Pending Review
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="hard-shadow rounded-xl border-2 border-ink bg-white p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="inline-flex items-center gap-1.5 rounded-full border border-ink bg-[#ffde4d] px-2.5 py-0.5 text-xs font-black uppercase tracking-wider text-ink">
              <ShieldCheck className="size-3.5" />
              SSKS Admin Workbench
            </div>
            <h1 className="mt-2 text-2xl font-black text-ink sm:text-3xl">
              Refine &amp; Verify Candidate Relationships
            </h1>
            <p className="mt-1 text-xs text-muted sm:text-sm">
              Inspect candidate relationships, refine types and directional hierarchy, record supporting evidence, and publish canonical ontology records.
            </p>
          </div>

          <button onClick={handleRefresh} disabled={isRefreshing} className="hard-shadow-sm flex shrink-0 items-center justify-center gap-2 whitespace-nowrap self-start rounded-lg border-2 border-ink bg-[#fff9f2] px-4 py-2 text-xs font-bold text-ink hover:bg-[#ffefdc] disabled:opacity-50 cursor-pointer sm:self-auto">
            <RotateCcw className={`size-3.5 shrink-0 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh Queue
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="mt-6 flex flex-wrap gap-2 border-b-2 border-ink/10 pb-1">
          <button
            onClick={() => setActiveTab("RELATIONSHIPS")}
            className={`hard-shadow-sm flex items-center gap-2 rounded-lg border-2 px-4 py-2 text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${activeTab === "RELATIONSHIPS"
              ? "border-ink bg-[#7df9ff] text-ink translate-y-0.5"
              : "border-ink/20 bg-[#fff9f2] text-muted hover:border-ink hover:bg-white hover:text-ink"
              }`}
          >
            <span>Relationship Candidates</span>
            <span className="rounded-full bg-white/80 px-2 py-0.2 text-[10px] font-bold border border-ink/20">
              {candidates.length}
            </span>
            {pendingCount > 0 && (
              <span className="rounded-full bg-[#eba0ff] px-1.5 py-0.2 text-[10px] font-extrabold text-ink border border-ink/30">
                {pendingCount} Pending
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("ENTITIES")}
            className={`hard-shadow-sm flex items-center gap-2 rounded-lg border-2 px-4 py-2 text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${activeTab === "ENTITIES"
              ? "border-ink bg-[#7df9ff] text-ink translate-y-0.5"
              : "border-ink/20 bg-[#fff9f2] text-muted hover:border-ink hover:bg-white hover:text-ink"
              }`}
          >
            <span>Entity Candidates</span>
            <span className="rounded bg-[#ffde4d] px-1.5 py-0.2 text-[10px] font-bold text-ink border border-ink/30">
              Coming Soon
            </span>
          </button>
        </div>

        {/* Search & Status Filters for Relationship Candidates */}
        {activeTab === "RELATIONSHIPS" && (
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
              <input
                type="text"
                placeholder="Search candidates by skill name, ID, relationship type, or evidence..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setPage(1);
                }}
                className="hard-shadow-sm w-full rounded-lg border-2 border-ink bg-[#fff9f2] py-2 pl-9 pr-3 text-xs font-medium text-ink placeholder:text-muted focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="size-4 text-muted" />
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="hard-shadow-sm rounded-lg border-2 border-ink bg-white px-3 py-2 text-xs font-bold text-ink focus:outline-none cursor-pointer"
              >
                <option value="ALL">All Review Statuses ({candidates.length})</option>
                <option value="PENDING">Pending Only ({pendingCount})</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
              </select>
            </div>
          </div>
        )}

        {notification && (
          <div
            className={`mt-4 flex items-center justify-between rounded-lg border-2 border-ink p-3 text-xs font-bold ${notification.type === "success" ? "bg-[#d0ffa4] text-ink" : "bg-[#ffbaba] text-ink"
              }`}
          >
            <span>{notification.message}</span>
            <button
              onClick={() => setNotification(null)}
              className="ml-2 underline text-xs cursor-pointer font-black"
            >
              Dismiss
            </button>
          </div>
        )}

        {skillsError && (
          <div className="mt-4 flex items-center justify-between rounded-lg border-2 border-ink bg-[#ffbaba] p-3 text-xs font-bold text-ink">
            <div className="flex items-center gap-2">
              <AlertCircle className="size-4 text-ink shrink-0" />
              <span>Skill catalogue error: {skillsError}. Displaying canonical IDs.</span>
            </div>
            <button
              onClick={() => setSkillsError(null)}
              className="ml-2 underline text-xs cursor-pointer font-black"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>

      {/* TAB 1: RELATIONSHIP CANDIDATES */}
      {activeTab === "RELATIONSHIPS" && (
        <div className="space-y-4">
          {paginatedCandidates.length === 0 ? (
            <div className="hard-shadow rounded-xl border-2 border-ink bg-white p-8 text-center text-muted">
              <p className="font-bold">No candidate relationships found matching your filters</p>
            </div>
          ) : (
            paginatedCandidates.map((cand) => {
              const isPending = cand.review_status === "PENDING";

              return (
                <div
                  key={cand.candidate_relationship_id}
                  className="hard-shadow rounded-xl border-2 border-ink bg-white p-5 transition-transform hover:-translate-y-0.5"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-black text-ink">
                          {cand.candidate_relationship_id}
                        </span>
                        {getStatusBadge(cand.review_status)}

                        {cand.canonical_relationship_id && (
                          <span className="hard-shadow-sm rounded bg-[#edddfc] border border-ink px-2 py-0.5 text-[10px] font-black uppercase text-ink">
                            Canonical: {cand.canonical_relationship_id}
                          </span>
                        )}

                        {cand.confidence_score !== null && (
                          <span className="hard-shadow-sm rounded bg-[#fff9f2] border border-ink px-2 py-0.5 text-[11px] font-bold text-ink">
                            Confidence: {Math.round(cand.confidence_score * 100)}%
                          </span>
                        )}

                        {cand.source_id && (
                          <span className="text-[11px] text-muted">
                            Source: {cand.source_id}
                          </span>
                        )}
                      </div>

                      {/* Relationship Visual Representation: Source Skill → Readable Relation → Target Skill */}
                      <div className="flex flex-wrap items-center gap-2.5 pt-1.5">
                        {renderSkillBadge(cand.source_skill_id, skillsMap, isSkillsLoading)}

                        <span
                          className={`hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink px-3 py-1.5 text-xs font-black uppercase text-ink ${getRelationshipBadgeColor(
                            cand.proposed_relationship_type,
                          )}`}
                          title={`Relationship type: ${cand.proposed_relationship_type}`}
                        >
                          <span>{formatRelationshipType(cand.proposed_relationship_type)}</span>
                          <ArrowRight className="size-3.5 stroke-[2.5]" />
                        </span>

                        {renderSkillBadge(cand.target_skill_id, skillsMap, isSkillsLoading)}
                      </div>

                      {/* Evidence & Provenance Details if Available */}
                      {(cand.evidence_description || cand.evidence_url || cand.review_note) && (
                        <div className="mt-2 space-y-1 text-xs">
                          {cand.evidence_description && (
                            <p className="text-ink/90 font-medium">
                              <span className="font-bold text-ink">Evidence:</span> {cand.evidence_description}
                            </p>
                          )}
                          {cand.evidence_url && (
                            <p className="flex items-center gap-1 text-blue-700">
                              <span className="font-bold text-ink">Documentation:</span>
                              <a
                                href={cand.evidence_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 underline hover:text-blue-900 font-bold"
                              >
                                {cand.evidence_url}
                                <ExternalLink className="size-3" />
                              </a>
                            </p>
                          )}
                          {cand.review_note && (
                            <p className="text-muted italic">
                              <span className="font-semibold not-italic">Review Comment:</span> &ldquo;{cand.review_note}&rdquo;
                            </p>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Review Actions */}
                    <div className="flex items-center gap-2 self-end lg:self-auto shrink-0">
                      {isPending ? (
                        <>
                          <button
                            onClick={() => handleOpenWorkbench(cand, "REFINE_AND_VERIFY")}
                            className="hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#d0ffa4] px-4 py-2 text-xs font-black text-ink transition-transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
                          >
                            <ShieldCheck className="size-3.5" />
                            Refine &amp; Verify
                          </button>
                          <button
                            onClick={() => handleOpenWorkbench(cand, "REJECT")}
                            className="hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#ffbaba] px-3.5 py-2 text-xs font-black text-ink transition-transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
                          >
                            <XCircle className="size-3.5" />
                            Reject
                          </button>
                        </>
                      ) : (
                        <div className="text-right text-xs">
                          <span className="font-bold text-muted block">
                            Reviewed {cand.reviewed_at ? new Date(cand.reviewed_at).toLocaleDateString() : ""}
                          </span>
                          {cand.reviewed_by && (
                            <span className="text-[11px] text-muted block">
                              by {cand.reviewed_by}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {/* Pagination Controls */}
          <div className="flex items-center justify-between border-t-2 border-ink bg-white p-4 rounded-xl hard-shadow text-xs">
            <span className="font-semibold text-muted">
              Showing {filteredCandidates.length === 0 ? 0 : (page - 1) * ITEMS_PER_PAGE + 1}–
              {Math.min(page * ITEMS_PER_PAGE, filteredCandidates.length)} of {filteredCandidates.length} candidate relationships
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="hard-shadow-sm flex items-center gap-1 rounded border-2 border-ink bg-white px-2.5 py-1 font-bold text-ink hover:bg-[#fff9f2] disabled:cursor-not-allowed disabled:opacity-40 cursor-pointer"
              >
                <ChevronLeft className="size-3.5" />
                Prev
              </button>
              <span className="font-bold text-ink">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="hard-shadow-sm flex items-center gap-1 rounded border-2 border-ink bg-white px-2.5 py-1 font-bold text-ink hover:bg-[#fff9f2] disabled:cursor-not-allowed disabled:opacity-40 cursor-pointer"
              >
                Next
                <ChevronRight className="size-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ENTITY CANDIDATES */}
      {activeTab === "ENTITIES" && (
        <div className="hard-shadow rounded-2xl border-2 border-ink bg-[#fff9f2] p-8 text-center sm:p-12">
          <div className="mx-auto flex size-14 items-center justify-center rounded-2xl border-2 border-ink bg-[#ffde4d] hard-shadow-sm">
            <Sparkles className="size-7 text-ink" />
          </div>

          <h3 className="mt-4 text-xl font-black text-ink sm:text-2xl">
            Entity Candidates Workflow Coming Soon
          </h3>
          <p className="mx-auto mt-2 max-w-lg text-xs font-medium text-muted sm:text-sm">
            Automated extraction and proposal review pipelines for new canonical skills and industry roles are currently in development.
            In this release, canonical entities are managed directly via Shared Knowledge Management.
          </p>

          <div className="mt-6 inline-flex items-center gap-2 rounded-full border-2 border-ink bg-[#edddfc] px-4 py-1.5 text-xs font-bold text-ink hard-shadow-sm">
            <span className="size-2 rounded-full bg-purple-600 animate-pulse" />
            Scheduled for Next Milestone Release
          </div>
        </div>
      )}

      {/* EXTRACTED MODAL COMPONENT (Separation of Concerns) */}
      <CandidateRefineModal
        isOpen={activeCandidate !== null}
        candidate={activeCandidate}
        initialMode={modalMode}
        skillsMap={skillsMap}
        reviewerId={reviewerId}
        onClose={() => setActiveCandidate(null)}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
}
