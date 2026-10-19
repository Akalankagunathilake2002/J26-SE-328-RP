"use client";

import { useState, useMemo } from "react";
import type { CandidateRelationshipItem } from "@/lib/ssksApi";
import { reviewCandidateRelationship, fetchSsksCandidateRelationships } from "@/lib/ssksApi";
import {
  Clock,
  CheckCircle2,
  XCircle,
  ArrowRight,
  AlertCircle,
  Loader2,
  Filter,
  Search,
  RotateCcw,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";

interface AdminCandidatesViewProps {
  initialCandidates: CandidateRelationshipItem[];
  reviewerId?: string;
}

type CandidateTab = "RELATIONSHIPS" | "ENTITIES";

const ITEMS_PER_PAGE = 10;

export function AdminCandidatesView({
  initialCandidates,
  reviewerId = "admin-reviewer",
}: AdminCandidatesViewProps) {
  const [activeTab, setActiveTab] = useState<CandidateTab>("RELATIONSHIPS");
  const [candidates, setCandidates] = useState<CandidateRelationshipItem[]>(initialCandidates);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [activeReviewCandidate, setActiveReviewCandidate] = useState<{
    candidate: CandidateRelationshipItem;
    action: "APPROVE" | "REJECT";
  } | null>(null);
  const [reviewNote, setReviewNote] = useState("");
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const pendingCount = useMemo(() => {
    return candidates.filter((c) => c.review_status === "PENDING").length;
  }, [candidates]);

  // Refresh candidate relationships from API
  const handleRefresh = async () => {
    setIsRefreshing(true);
    setNotification(null);
    try {
      const data = await fetchSsksCandidateRelationships({ limit: 500 });
      setCandidates(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to refresh candidates";
      setNotification({ type: "error", message: msg });
    } finally {
      setIsRefreshing(false);
    }
  };

  const filteredCandidates = useMemo(() => {
    return candidates.filter((item) => {
      const matchesStatus =
        statusFilter === "ALL" ? true : item.review_status === statusFilter;

      const q = searchTerm.toLowerCase().trim();
      const matchesSearch =
        !q ||
        item.source_skill_id.toLowerCase().includes(q) ||
        item.target_skill_id.toLowerCase().includes(q) ||
        item.proposed_relationship_type.toLowerCase().includes(q) ||
        item.candidate_relationship_id.toLowerCase().includes(q) ||
        (item.review_note && item.review_note.toLowerCase().includes(q));

      return matchesStatus && matchesSearch;
    });
  }, [candidates, statusFilter, searchTerm]);

  // 10 items per page pagination
  const totalPages = Math.ceil(filteredCandidates.length / ITEMS_PER_PAGE) || 1;
  const paginatedCandidates = useMemo(() => {
    const start = (page - 1) * ITEMS_PER_PAGE;
    return filteredCandidates.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredCandidates, page]);

  const handleOpenReviewModal = (
    candidate: CandidateRelationshipItem,
    action: "APPROVE" | "REJECT",
  ) => {
    setActiveReviewCandidate({ candidate, action });
    setReviewNote(
      action === "APPROVE"
        ? "Verified and approved by administrator"
        : "Rejected by administrator during taxonomy review",
    );
  };

  const handleSubmitReview = async () => {
    if (!activeReviewCandidate) return;

    const { candidate, action } = activeReviewCandidate;
    setProcessingId(candidate.candidate_relationship_id);
    setNotification(null);

    try {
      const updated = await reviewCandidateRelationship(
        candidate.candidate_relationship_id,
        {
          action,
          review_note: reviewNote.trim() || undefined,
        },
        reviewerId,
      );

      // Update local state with reviewed candidate
      setCandidates((prev) =>
        prev.map((c) =>
          c.candidate_relationship_id === candidate.candidate_relationship_id ? updated : c,
        ),
      );

      setNotification({
        type: "success",
        message: `Candidate ${candidate.candidate_relationship_id} was successfully ${
          action === "APPROVE" ? "approved & verified into ontology" : "rejected"
        }.`,
      });
      setActiveReviewCandidate(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to review candidate";
      setNotification({
        type: "error",
        message,
      });
    } finally {
      setProcessingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full border border-ink bg-[#d0ffa4] px-2.5 py-0.5 text-xs font-black uppercase text-ink">
            <CheckCircle2 className="size-3.5" />
            Approved
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
              Taxonomy Ingestion Queue
            </div>
            <h1 className="mt-2 text-2xl font-black text-ink sm:text-3xl">
              Candidate Management
            </h1>
            <p className="mt-1 text-xs text-muted sm:text-sm">
              Review and verify or reject proposed knowledge-base records
            </p>
          </div>

          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="hard-shadow-sm flex items-center gap-1.5 self-start sm:self-auto rounded-lg border-2 border-ink bg-[#fff9f2] px-3 py-2 text-xs font-bold text-ink hover:bg-[#ffefdc] disabled:opacity-50"
          >
            <RotateCcw className={`size-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh Queue
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="mt-6 flex flex-wrap gap-2 border-b-2 border-ink/10 pb-1">
          <button
            onClick={() => setActiveTab("RELATIONSHIPS")}
            className={`hard-shadow-sm flex items-center gap-2 rounded-lg border-2 px-4 py-2 text-xs font-black uppercase tracking-wider transition-all ${
              activeTab === "RELATIONSHIPS"
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
            className={`hard-shadow-sm flex items-center gap-2 rounded-lg border-2 px-4 py-2 text-xs font-black uppercase tracking-wider transition-all ${
              activeTab === "ENTITIES"
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
                placeholder="Search candidates by skill ID or type..."
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
                className="hard-shadow-sm rounded-lg border-2 border-ink bg-white px-3 py-2 text-xs font-bold text-ink focus:outline-none"
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
            className={`mt-4 flex items-center justify-between rounded-lg border-2 border-ink p-3 text-xs font-bold ${
              notification.type === "success" ? "bg-[#d0ffa4] text-ink" : "bg-[#ffbaba] text-ink"
            }`}
          >
            <span>{notification.message}</span>
            <button onClick={() => setNotification(null)} className="ml-2 underline text-xs">
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
              const isBusy = processingId === cand.candidate_relationship_id;

              return (
                <div
                  key={cand.candidate_relationship_id}
                  className="hard-shadow rounded-xl border-2 border-ink bg-white p-5 transition-transform hover:-translate-y-0.5"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-ink">
                          {cand.candidate_relationship_id}
                        </span>
                        {getStatusBadge(cand.review_status)}
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

                      {/* Relationship Visual Representation */}
                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        <span className="hard-shadow-sm rounded border-2 border-ink bg-[#fff9f2] px-3 py-1 font-mono text-xs font-bold text-ink">
                          {cand.source_skill_id}
                        </span>
                        <span className="hard-shadow-sm flex items-center gap-1 rounded border-2 border-ink bg-[#7df9ff] px-2.5 py-1 text-xs font-black uppercase text-ink">
                          {cand.proposed_relationship_type.replace(/_/g, " ")}
                          <ArrowRight className="size-3.5" />
                        </span>
                        <span className="hard-shadow-sm rounded border-2 border-ink bg-[#fff9f2] px-3 py-1 font-mono text-xs font-bold text-ink">
                          {cand.target_skill_id}
                        </span>
                      </div>

                      {cand.review_note && (
                        <p className="text-xs text-muted italic">
                          Review Note: &ldquo;{cand.review_note}&rdquo;
                        </p>
                      )}
                    </div>

                    {/* Review Actions */}
                    <div className="flex items-center gap-2 self-end lg:self-auto">
                      {isPending ? (
                        <>
                          <button
                            onClick={() => handleOpenReviewModal(cand, "APPROVE")}
                            disabled={processingId !== null}
                            className="hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#d0ffa4] px-4 py-2 text-xs font-black text-ink transition-transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50"
                          >
                            {isBusy ? (
                              <Loader2 className="size-3.5 animate-spin" />
                            ) : (
                              <CheckCircle2 className="size-3.5" />
                            )}
                            Approve
                          </button>
                          <button
                            onClick={() => handleOpenReviewModal(cand, "REJECT")}
                            disabled={processingId !== null}
                            className="hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#ffbaba] px-4 py-2 text-xs font-black text-ink transition-transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50"
                          >
                            <XCircle className="size-3.5" />
                            Reject
                          </button>
                        </>
                      ) : (
                        <div className="text-right">
                          <span className="text-[11px] font-bold text-muted">
                            Reviewed {cand.reviewed_at ? new Date(cand.reviewed_at).toLocaleDateString() : ""}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {/* Pagination Controls (10 records per page) */}
          <div className="flex items-center justify-between border-t-2 border-ink bg-white p-4 rounded-xl hard-shadow text-xs">
            <span className="font-semibold text-muted">
              Showing {filteredCandidates.length === 0 ? 0 : (page - 1) * ITEMS_PER_PAGE + 1}–
              {Math.min(page * ITEMS_PER_PAGE, filteredCandidates.length)} of {filteredCandidates.length} candidate relationships
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="hard-shadow-sm flex items-center gap-1 rounded border-2 border-ink bg-white px-2.5 py-1 font-bold text-ink hover:bg-[#fff9f2] disabled:cursor-not-allowed disabled:opacity-40"
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
                className="hard-shadow-sm flex items-center gap-1 rounded border-2 border-ink bg-white px-2.5 py-1 font-bold text-ink hover:bg-[#fff9f2] disabled:cursor-not-allowed disabled:opacity-40"
              >
                Next
                <ChevronRight className="size-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ENTITY CANDIDATES (Coming Soon Placeholder) */}
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

      {/* Review Confirmation Modal */}
      {activeReviewCandidate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="hard-shadow w-full max-w-md rounded-xl border-2 border-ink bg-white p-6">
            <div className="flex items-center gap-2">
              <AlertCircle className="size-5 text-ink" />
              <h3 className="text-base font-black text-ink">
                Confirm {activeReviewCandidate.action === "APPROVE" ? "Approval" : "Rejection"}
              </h3>
            </div>

            <p className="mt-2 text-xs text-muted">
              {activeReviewCandidate.action === "APPROVE"
                ? `Approving will verify relationship ${activeReviewCandidate.candidate.source_skill_id} → ${activeReviewCandidate.candidate.target_skill_id} and add it to the SSKS ontology graph.`
                : `Rejecting will discard relationship ${activeReviewCandidate.candidate.candidate_relationship_id} from ontology inclusion.`}
            </p>

            <div className="mt-4">
              <label className="block text-xs font-bold text-ink">Review Note (Optional)</label>
              <textarea
                value={reviewNote}
                onChange={(e) => setReviewNote(e.target.value)}
                placeholder="Add audit note or reason..."
                rows={3}
                className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2.5 text-xs text-ink placeholder:text-muted focus:outline-none"
              />
            </div>

            <div className="mt-5 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setActiveReviewCandidate(null)}
                className="hard-shadow-sm rounded-lg border-2 border-ink bg-white px-4 py-2 text-xs font-bold text-ink hover:bg-[#fff9f2]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmitReview}
                disabled={processingId !== null}
                className={`hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink px-4 py-2 text-xs font-black text-ink ${
                  activeReviewCandidate.action === "APPROVE"
                    ? "bg-[#d0ffa4] hover:bg-[#b8f582]"
                    : "bg-[#ffbaba] hover:bg-[#fa9c9c]"
                }`}
              >
                {processingId ? <Loader2 className="size-3.5 animate-spin" /> : <CheckCircle2 className="size-3.5" />}
                Confirm {activeReviewCandidate.action === "APPROVE" ? "Verification" : "Rejection"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
