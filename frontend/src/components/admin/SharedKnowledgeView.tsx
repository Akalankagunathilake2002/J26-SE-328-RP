"use client";

import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import {
  fetchSsksDomains,
  fetchSsksRolesAll,
  fetchSsksSkillsAll,
  fetchSsksRelationshipsAll,
  createSsksDomain,
  createSsksRole,
  createSsksSkill,
  createSsksRelationship,
  type DomainItem,
  type RoleItem,
  type SkillItem,
  type SkillRelationshipItem,
  type SkillRelationshipType,
} from "@/lib/ssksApi";
import {
  Search,
  Plus,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  X,
  Info,
} from "lucide-react";

type ActiveTab = "DOMAINS" | "ROLES" | "SKILLS" | "RELATIONSHIPS";

const ITEMS_PER_PAGE = 10;

// Searchable dropdown for selecting existing canonical skills without manual ID entry.
function SkillSearchSelect({
  label,
  value,
  onChange,
  skills,
  excludeId,
  placeholder = "Select a canonical skill...",
}: {
  label: string;
  value: string;
  onChange: (skillId: string) => void;
  skills: SkillItem[];
  excludeId?: string;
  placeholder?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedSkill = useMemo(
    () => skills.find((s) => s.skill_id === value),
    [skills, value],
  );

  const filteredSkills = useMemo(() => {
    const q = query.toLowerCase().trim();
    return skills
      .filter((s) => {
        if (excludeId && s.skill_id === excludeId) return false;
        if (!q) return true;
        return (
          s.skill_id.toLowerCase().includes(q) ||
          s.preferred_name.toLowerCase().includes(q)
        );
      })
      .slice(0, 80);
  }, [skills, query, excludeId]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block text-xs font-bold text-ink">
        {label} <span className="text-red-500">*</span>
      </label>

      <div
        onClick={() => setIsOpen((prev) => !prev)}
        className="hard-shadow-sm mt-1 flex cursor-pointer items-center justify-between rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs font-bold text-ink hover:bg-white"
      >
        {selectedSkill ? (
          <div className="flex items-center gap-1.5 truncate">
            <span className="font-mono text-ink bg-white px-1.5 py-0.5 rounded border border-ink/30">
              {selectedSkill.skill_id}
            </span>
            <span className="text-ink truncate">· {selectedSkill.preferred_name}</span>
          </div>
        ) : (
          <span className="text-muted font-normal">{placeholder}</span>
        )}

        <div className="flex items-center gap-1 ml-2">
          {selectedSkill && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onChange("");
              }}
              className="p-0.5 hover:bg-black/10 rounded"
              title="Clear selection"
            >
              <X className="size-3 text-muted hover:text-ink" />
            </button>
          )}
          <Search className="size-3.5 text-muted" />
        </div>
      </div>

      {isOpen && (
        <div className="hard-shadow absolute left-0 right-0 top-full z-50 mt-1 max-h-64 overflow-hidden rounded-lg border-2 border-ink bg-white shadow-xl">
          <div className="border-b-2 border-ink/10 p-2 bg-[#fff9f2]">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted" />
              <input
                type="text"
                autoFocus
                placeholder="Search by skill ID or preferred name..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full rounded border border-ink/40 bg-white py-1.5 pl-8 pr-2 text-xs font-medium text-ink placeholder:text-muted focus:outline-none focus:border-ink"
              />
            </div>
          </div>

          <div className="max-h-48 overflow-y-auto divide-y divide-ink/5">
            {filteredSkills.length === 0 ? (
              <div className="p-3 text-center text-xs text-muted">
                No matching canonical skills found
              </div>
            ) : (
              filteredSkills.map((s) => (
                <div
                  key={s.skill_id}
                  onClick={() => {
                    onChange(s.skill_id);
                    setIsOpen(false);
                    setQuery("");
                  }}
                  className={`flex cursor-pointer items-center justify-between px-3 py-2 text-xs transition-colors hover:bg-[#fff9f2] ${
                    value === s.skill_id ? "bg-[#d0ffa4] font-bold" : ""
                  }`}
                >
                  <div className="flex items-center gap-1.5 truncate">
                    <span className="font-mono font-bold text-ink bg-white px-1 py-0.5 rounded border border-ink/30 text-[11px]">
                      {s.skill_id}
                    </span>
                    <span className="font-semibold text-ink truncate">· {s.preferred_name}</span>
                  </div>
                  <span className="ml-2 text-[10px] font-bold uppercase tracking-wider text-muted whitespace-nowrap">
                    {s.skill_type.replace(/_/g, " ").toLowerCase()}
                  </span>
                </div>
              ))
            )}
          </div>
          {skills.length > 80 && (
            <div className="border-t border-ink/10 bg-[#f5ecd8] px-2.5 py-1 text-[10px] text-muted">
              Showing top {filteredSkills.length} matches of {skills.length} skills
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface SharedKnowledgeViewProps {
  initialDomains: DomainItem[];
  initialRoles: RoleItem[];
  initialSkills: SkillItem[];
  initialRelationships: SkillRelationshipItem[];
}

export function SharedKnowledgeView({
  initialDomains,
  initialRoles,
  initialSkills,
  initialRelationships,
}: SharedKnowledgeViewProps) {
  const [activeTab, setActiveTab] = useState<ActiveTab>("DOMAINS");

  // Data states
  const [domains, setDomains] = useState<DomainItem[]>(initialDomains);
  const [roles, setRoles] = useState<RoleItem[]>(initialRoles);
  const [skills, setSkills] = useState<SkillItem[]>(initialSkills);
  const [relationships, setRelationships] = useState<SkillRelationshipItem[]>(initialRelationships);

  // Filter & pagination states
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form states without manual ID inputs (IDs generated on backend)
  const [domainForm, setDomainForm] = useState({
    name: "",
    code: "",
    description: "",
  });

  const [roleForm, setRoleForm] = useState({
    preferred_name: "",
    description: "",
    domain_id: "",
  });

  const [skillForm, setSkillForm] = useState({
    preferred_name: "",
    description: "",
    skill_type: "PROGRAMMING_SKILL",
    skill_nature: "TECHNICAL",
    domain_id: "",
  });

  const [relForm, setRelForm] = useState({
    source_skill_id: "",
    target_skill_id: "",
    relationship_type: "RELATED_TO" as SkillRelationshipType,
    evidence_note: "",
  });

  // Fast map lookup for skill preferred names
  const skillsMap = useMemo(() => new Map(skills.map((s) => [s.skill_id, s.preferred_name])), [skills]);

  // Reset page and search when switching tabs
  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab);
    setSearchTerm("");
    setPage(1);
    setFeedback(null);
    setError(null);
  };

  // Reload data for active tab using complete batch pagination
  const refreshActiveTabData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (activeTab === "DOMAINS") {
        const data = await fetchSsksDomains();
        setDomains(data);
      } else if (activeTab === "ROLES") {
        const data = await fetchSsksRolesAll();
        setRoles(data);
      } else if (activeTab === "SKILLS") {
        const data = await fetchSsksSkillsAll();
        setSkills(data);
      } else if (activeTab === "RELATIONSHIPS") {
        const data = await fetchSsksRelationshipsAll();
        setRelationships(data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load data";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [activeTab]);

  // Filtered dataset for active tab
  const filteredData = useMemo(() => {
    const q = searchTerm.toLowerCase().trim();
    if (activeTab === "DOMAINS") {
      return domains.filter(
        (d) =>
          d.name.toLowerCase().includes(q) ||
          d.domain_id.toLowerCase().includes(q) ||
          d.code.toLowerCase().includes(q),
      );
    }
    if (activeTab === "ROLES") {
      return roles.filter(
        (r) =>
          r.preferred_name.toLowerCase().includes(q) ||
          r.role_id.toLowerCase().includes(q) ||
          (r.description && r.description.toLowerCase().includes(q)),
      );
    }
    if (activeTab === "SKILLS") {
      return skills.filter(
        (s) =>
          s.preferred_name.toLowerCase().includes(q) ||
          s.skill_id.toLowerCase().includes(q) ||
          s.skill_type.toLowerCase().includes(q),
      );
    }
    if (activeTab === "RELATIONSHIPS") {
      return relationships.filter(
        (rel) =>
          rel.source_skill_id.toLowerCase().includes(q) ||
          rel.target_skill_id.toLowerCase().includes(q) ||
          rel.relationship_type.toLowerCase().includes(q) ||
          rel.relationship_id.toLowerCase().includes(q) ||
          (skillsMap.get(rel.source_skill_id) || "").toLowerCase().includes(q) ||
          (skillsMap.get(rel.target_skill_id) || "").toLowerCase().includes(q),
      );
    }
    return [];
  }, [activeTab, domains, roles, skills, relationships, searchTerm, skillsMap]);

  // 10 items per page pagination
  const totalPages = Math.ceil(filteredData.length / ITEMS_PER_PAGE) || 1;
  const paginatedData = useMemo(() => {
    const start = (page - 1) * ITEMS_PER_PAGE;
    return filteredData.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredData, page]);

  // Handle Create submission
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);

    try {
      if (activeTab === "DOMAINS") {
        if (!domainForm.name.trim() || !domainForm.code.trim()) {
          throw new Error("Domain Name and Code are required.");
        }
        const created = await createSsksDomain({
          name: domainForm.name.trim(),
          code: domainForm.code.trim().toUpperCase(),
          description: domainForm.description.trim() || undefined,
        });
        setFeedback({
          type: "success",
          message: `Domain "${created.name}" created successfully with ID: ${created.domain_id}`,
        });
        setDomainForm({ name: "", code: "", description: "" });
      } else if (activeTab === "ROLES") {
        if (!roleForm.preferred_name.trim()) {
          throw new Error("Role Title / Preferred Name is required.");
        }
        const created = await createSsksRole({
          preferred_name: roleForm.preferred_name.trim(),
          description: roleForm.description.trim() || undefined,
          domain_id: roleForm.domain_id || undefined,
        });
        setFeedback({
          type: "success",
          message: `Role "${created.preferred_name}" created successfully with ID: ${created.role_id}`,
        });
        setRoleForm({ preferred_name: "", description: "", domain_id: "" });
      } else if (activeTab === "SKILLS") {
        if (!skillForm.preferred_name.trim()) {
          throw new Error("Skill Preferred Name is required.");
        }
        const created = await createSsksSkill({
          preferred_name: skillForm.preferred_name.trim(),
          description: skillForm.description.trim() || undefined,
          skill_type: skillForm.skill_type,
          skill_nature: skillForm.skill_nature,
          domain_id: skillForm.domain_id || undefined,
        });
        setFeedback({
          type: "success",
          message: `Skill "${created.preferred_name}" created successfully with ID: ${created.skill_id}`,
        });
        setSkillForm({
          preferred_name: "",
          description: "",
          skill_type: "PROGRAMMING_SKILL",
          skill_nature: "TECHNICAL",
          domain_id: "",
        });
      } else if (activeTab === "RELATIONSHIPS") {
        if (!relForm.source_skill_id.trim() || !relForm.target_skill_id.trim()) {
          throw new Error("Both Source Skill and Target Skill must be selected.");
        }
        if (relForm.source_skill_id.trim() === relForm.target_skill_id.trim()) {
          throw new Error("Source skill and Target skill must be different.");
        }
        const created = await createSsksRelationship({
          source_skill_id: relForm.source_skill_id.trim(),
          target_skill_id: relForm.target_skill_id.trim(),
          relationship_type: relForm.relationship_type,
          evidence_note: relForm.evidence_note.trim() || undefined,
        });
        setFeedback({
          type: "success",
          message: `Verified relationship created with ID: ${created.relationship_id} (${created.source_skill_id} → ${created.target_skill_id})`,
        });
        setRelForm({
          source_skill_id: "",
          target_skill_id: "",
          relationship_type: "RELATED_TO",
          evidence_note: "",
        });
      }

      setIsModalOpen(false);
      await refreshActiveTabData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Submission failed";
      setFormError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getRelationshipBadgeColor = (type: string) => {
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
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="hard-shadow rounded-xl border-2 border-ink bg-white p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="inline-flex items-center gap-1.5 rounded-full border border-ink bg-[#d0ffa4] px-2.5 py-0.5 text-xs font-black uppercase tracking-wider text-ink">
              <ShieldCheck className="size-3.5" />
              SSKS Central Knowledge Base
            </div>
            <h1 className="mt-2 text-2xl font-black text-ink sm:text-3xl">
              Shared Knowledge Management
            </h1>
            <p className="mt-1 text-xs text-muted sm:text-sm">
              Manage domains, roles, skills and semantic relationships
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={refreshActiveTabData}
              disabled={isLoading}
              title="Refresh current tab data"
              className="hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#fff9f2] px-3 py-2 text-xs font-bold text-ink hover:bg-[#ffefdc] disabled:opacity-50"
            >
              <RotateCcw className={`size-3.5 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <button
              onClick={() => {
                setFormError(null);
                setIsModalOpen(true);
              }}
              className="hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#ffde4d] px-4 py-2 text-xs font-black text-ink transition-transform hover:-translate-y-0.5"
            >
              <Plus className="size-4" />
              Create New {activeTab.slice(0, -1)}
            </button>
          </div>
        </div>

        {/* Action Feedback Message */}
        {feedback && (
          <div
            className={`mt-4 flex items-center justify-between rounded-lg border-2 border-ink p-3 text-xs font-bold ${
              feedback.type === "success" ? "bg-[#d0ffa4] text-ink" : "bg-[#ffbaba] text-ink"
            }`}
          >
            <span>{feedback.message}</span>
            <button onClick={() => setFeedback(null)} className="ml-2 underline text-xs">
              Dismiss
            </button>
          </div>
        )}

        {/* Tab Navigation Controls */}
        <div className="mt-6 flex flex-wrap gap-2 border-b-2 border-ink/10 pb-1">
          {(
            [
              { id: "DOMAINS", label: "Domains", count: domains.length },
              { id: "ROLES", label: "Roles", count: roles.length },
              { id: "SKILLS", label: "Skills", count: skills.length },
              { id: "RELATIONSHIPS", label: "Relationships", count: relationships.length },
            ] as const
          ).map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`hard-shadow-sm flex items-center gap-2 rounded-lg border-2 px-4 py-2 text-xs font-black uppercase tracking-wider transition-all ${
                  isActive
                    ? "border-ink bg-[#7df9ff] text-ink translate-y-0.5"
                    : "border-ink/20 bg-[#fff9f2] text-muted hover:border-ink hover:bg-white hover:text-ink"
                }`}
              >
                <span>{tab.label}</span>
                <span className="rounded-full bg-white/80 px-1.5 py-0.2 text-[10px] font-bold border border-ink/20">
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search Bar */}
        <div className="mt-4 flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
            <input
              type="text"
              placeholder={`Search ${activeTab.toLowerCase()} by name or ID...`}
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="hard-shadow-sm w-full rounded-lg border-2 border-ink bg-[#fff9f2] py-2 pl-9 pr-3 text-xs font-medium text-ink placeholder:text-muted focus:outline-none"
            />
          </div>
          {searchTerm && (
            <button
              onClick={() => {
                setSearchTerm("");
                setPage(1);
              }}
              className="text-xs font-bold text-muted underline hover:text-ink"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Main Table Container */}
      <div className="hard-shadow overflow-hidden rounded-xl border-2 border-ink bg-white">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center p-12 text-muted">
            <Loader2 className="size-8 animate-spin text-ink" />
            <p className="mt-2 text-xs font-bold">Loading {activeTab.toLowerCase()}...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <AlertCircle className="mx-auto size-8 text-red-600 mb-2" />
            <p className="text-sm font-bold text-red-600">{error}</p>
            <button
              onClick={refreshActiveTabData}
              className="hard-shadow-sm mt-3 inline-block rounded border-2 border-ink bg-[#fff9f2] px-3 py-1.5 text-xs font-bold text-ink"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            {/* 1. DOMAINS TABLE */}
            {activeTab === "DOMAINS" && (
              <table className="w-full text-left text-xs">
                <thead className="border-b-2 border-ink bg-[#f5ecd8] font-bold text-ink uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Domain ID</th>
                    <th className="px-4 py-3">Name</th>
                    <th className="px-4 py-3">Code</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y-2 divide-ink/10">
                  {paginatedData.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-muted">
                        No domains found matching &ldquo;{searchTerm}&rdquo;
                      </td>
                    </tr>
                  ) : (
                    (paginatedData as DomainItem[]).map((d) => (
                      <tr key={d.domain_id} className="transition-colors hover:bg-[#fff9f2]">
                        <td className="whitespace-nowrap px-4 py-3.5 font-mono font-bold text-ink">
                          <span className="hard-shadow-sm inline-block rounded bg-[#fff9f2] px-2 py-0.5 border border-ink">
                            {d.domain_id}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 font-bold text-ink">{d.name}</td>
                        <td className="px-4 py-3.5 font-mono text-muted">{d.code}</td>
                        <td className="px-4 py-3.5">
                          <span className="inline-flex items-center gap-1 rounded-full border border-ink bg-[#d0ffa4] px-2 py-0.5 text-[10px] font-black uppercase text-ink">
                            <CheckCircle2 className="size-3" />
                            {d.status}
                          </span>
                        </td>
                        <td className="max-w-md px-4 py-3.5 text-muted">
                          {d.description || "No description provided."}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}

            {/* 2. ROLES TABLE */}
            {activeTab === "ROLES" && (
              <table className="w-full text-left text-xs">
                <thead className="border-b-2 border-ink bg-[#f5ecd8] font-bold text-ink uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Role ID</th>
                    <th className="px-4 py-3">Canonical Title</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Description</th>
                    <th className="px-4 py-3 text-right">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y-2 divide-ink/10">
                  {paginatedData.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-muted">
                        No roles found matching &ldquo;{searchTerm}&rdquo;
                      </td>
                    </tr>
                  ) : (
                    (paginatedData as RoleItem[]).map((r) => (
                      <tr key={r.role_id} className="transition-colors hover:bg-[#fff9f2]">
                        <td className="whitespace-nowrap px-4 py-3.5 font-mono font-bold text-ink">
                          <span className="hard-shadow-sm inline-block rounded bg-[#fff9f2] px-2 py-0.5 border border-ink">
                            {r.role_id}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 font-bold text-ink capitalize">{r.preferred_name}</td>
                        <td className="px-4 py-3.5">
                          <span className="inline-flex items-center gap-1 rounded-full border border-ink bg-[#d0ffa4] px-2 py-0.5 text-[10px] font-black uppercase text-ink">
                            <CheckCircle2 className="size-3" />
                            {r.status}
                          </span>
                        </td>
                        <td className="max-w-md px-4 py-3.5 text-muted">
                          <p className="line-clamp-2">{r.description || "No official description recorded."}</p>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5 text-right font-medium text-muted">
                          {r.created_at ? new Date(r.created_at).toLocaleDateString() : "—"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}

            {/* 3. SKILLS TABLE */}
            {activeTab === "SKILLS" && (
              <table className="w-full text-left text-xs">
                <thead className="border-b-2 border-ink bg-[#f5ecd8] font-bold text-ink uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Skill ID</th>
                    <th className="px-4 py-3">Preferred Name</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Nature</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y-2 divide-ink/10">
                  {paginatedData.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-muted">
                        No skills found matching &ldquo;{searchTerm}&rdquo;
                      </td>
                    </tr>
                  ) : (
                    (paginatedData as SkillItem[]).map((s) => (
                      <tr key={s.skill_id} className="transition-colors hover:bg-[#fff9f2]">
                        <td className="whitespace-nowrap px-4 py-3.5 font-mono font-bold text-ink">
                          <span className="hard-shadow-sm inline-block rounded bg-[#fff9f2] px-2 py-0.5 border border-ink">
                            {s.skill_id}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 font-bold text-ink">{s.preferred_name}</td>
                        <td className="whitespace-nowrap px-4 py-3.5">
                          <span className="hard-shadow-sm inline-block rounded border border-ink bg-[#edddfc] px-2 py-0.5 text-[10px] font-bold uppercase text-ink">
                            {s.skill_type.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5">
                          {s.skill_nature ? (
                            <span className="hard-shadow-sm inline-block rounded border border-ink bg-[#ffefdc] px-2 py-0.5 text-[10px] font-bold uppercase text-ink">
                              {s.skill_nature}
                            </span>
                          ) : (
                            <span className="text-muted">—</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5">
                          <span className="inline-flex items-center gap-1 rounded-full border border-ink bg-[#d0ffa4] px-2 py-0.5 text-[10px] font-black uppercase text-ink">
                            <CheckCircle2 className="size-3" />
                            {s.status}
                          </span>
                        </td>
                        <td className="max-w-xs px-4 py-3.5 text-muted">
                          <p className="line-clamp-2">{s.description || "No official description recorded."}</p>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}

            {/* 4. RELATIONSHIPS TABLE */}
            {activeTab === "RELATIONSHIPS" && (
              <table className="w-full text-left text-xs">
                <thead className="border-b-2 border-ink bg-[#f5ecd8] font-bold text-ink uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Relationship ID</th>
                    <th className="px-4 py-3">Source Skill</th>
                    <th className="px-4 py-3 text-center">Type</th>
                    <th className="px-4 py-3">Target Skill</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Evidence / Note</th>
                  </tr>
                </thead>
                <tbody className="divide-y-2 divide-ink/10">
                  {paginatedData.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-muted">
                        No relationships found matching &ldquo;{searchTerm}&rdquo;
                      </td>
                    </tr>
                  ) : (
                    (paginatedData as SkillRelationshipItem[]).map((rel) => (
                      <tr key={rel.relationship_id} className="transition-colors hover:bg-[#fff9f2]">
                        <td className="whitespace-nowrap px-4 py-3.5 font-mono font-bold text-ink">
                          <span className="hard-shadow-sm inline-block rounded bg-[#fff9f2] px-2 py-0.5 border border-ink">
                            {rel.relationship_id}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5 font-mono text-ink">
                          <span className="hard-shadow-sm inline-block rounded bg-[#fff9f2] px-2 py-0.5 border border-ink font-bold">
                            {rel.source_skill_id}
                          </span>
                          {skillsMap.get(rel.source_skill_id) && (
                            <span className="ml-1.5 font-sans font-semibold text-ink">
                              · {skillsMap.get(rel.source_skill_id)}
                            </span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5 text-center">
                          <span
                            className={`hard-shadow-sm inline-flex items-center gap-1.5 rounded border border-ink px-2.5 py-1 text-[11px] font-black uppercase text-ink ${getRelationshipBadgeColor(
                              rel.relationship_type,
                            )}`}
                          >
                            {rel.relationship_type.replace(/_/g, " ")}
                            <ArrowRight className="size-3" />
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5 font-mono text-ink">
                          <span className="hard-shadow-sm inline-block rounded bg-[#fff9f2] px-2 py-0.5 border border-ink font-bold">
                            {rel.target_skill_id}
                          </span>
                          {skillsMap.get(rel.target_skill_id) && (
                            <span className="ml-1.5 font-sans font-semibold text-ink">
                              · {skillsMap.get(rel.target_skill_id)}
                            </span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5">
                          <span className="inline-flex items-center gap-1 rounded-full border border-ink bg-[#d0ffa4] px-2 py-0.5 text-[10px] font-black uppercase text-ink">
                            <ShieldCheck className="size-3 text-ink" />
                            {rel.verification_status}
                          </span>
                        </td>
                        <td className="max-w-xs px-4 py-3.5 text-muted">
                          <p className="line-clamp-2">{rel.evidence_note || "System verified ontology relation"}</p>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Pagination Footer (10 records per page) */}
        <div className="flex items-center justify-between border-t-2 border-ink bg-[#f5ecd8] px-4 py-3 text-xs">
          <span className="font-semibold text-muted">
            Showing {filteredData.length === 0 ? 0 : (page - 1) * ITEMS_PER_PAGE + 1}–
            {Math.min(page * ITEMS_PER_PAGE, filteredData.length)} of {filteredData.length} records
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

      {/* CREATE NEW RECORD MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="hard-shadow max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border-2 border-ink bg-white p-6">
            <div className="flex items-center justify-between border-b-2 border-ink/10 pb-3">
              <h3 className="text-base font-black text-ink">
                Create New {activeTab.slice(0, -1)}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="rounded p-1 hover:bg-[#fff9f2]"
              >
                <X className="size-4 text-ink" />
              </button>
            </div>

            {formError && (
              <div className="mt-4 rounded-lg border-2 border-ink bg-[#ffbaba] p-3 text-xs font-bold text-ink">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="mt-4 space-y-4">
              {/* DOMAINS FORM */}
              {activeTab === "DOMAINS" && (
                <>
                  <div>
                    <label className="block text-xs font-bold text-ink">
                      Domain Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Data Science & Engineering"
                      value={domainForm.name}
                      onChange={(e) => setDomainForm({ ...domainForm, name: e.target.value })}
                      required
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs font-bold text-ink focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-ink">
                      Domain Code <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. DATA (used for canonical ID DOM-DATA)"
                      value={domainForm.code}
                      onChange={(e) => setDomainForm({ ...domainForm, code: e.target.value })}
                      required
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs font-mono font-bold text-ink focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-ink">Description</label>
                    <textarea
                      placeholder="Detailed domain description..."
                      value={domainForm.description}
                      onChange={(e) => setDomainForm({ ...domainForm, description: e.target.value })}
                      rows={2}
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs text-ink focus:outline-none"
                    />
                  </div>
                  <div className="flex items-start gap-1.5 rounded-lg border border-ink/20 bg-[#fff9f2] p-2.5 text-[11px] text-muted">
                    <Info className="size-4 shrink-0 text-ink mt-0.5" />
                    <span>Domain canonical ID (DOM-&#123;CODE&#125;) will be generated automatically by the backend.</span>
                  </div>
                </>
              )}

              {/* ROLES FORM */}
              {activeTab === "ROLES" && (
                <>
                  <div>
                    <label className="block text-xs font-bold text-ink">
                      Canonical Title <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Machine Learning Engineer"
                      value={roleForm.preferred_name}
                      onChange={(e) => setRoleForm({ ...roleForm, preferred_name: e.target.value })}
                      required
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs font-bold text-ink focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-ink">
                      Domain Association <span className="text-muted font-normal">(optional)</span>
                    </label>
                    <select
                      value={roleForm.domain_id}
                      onChange={(e) => setRoleForm({ ...roleForm, domain_id: e.target.value })}
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs font-bold text-ink focus:outline-none"
                    >
                      <option value="">None / Unassigned</option>
                      {domains.map((d) => (
                        <option key={d.domain_id} value={d.domain_id}>
                          {d.name} ({d.code})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-ink">Description</label>
                    <textarea
                      placeholder="Official career role responsibilities..."
                      value={roleForm.description}
                      onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
                      rows={2}
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs text-ink focus:outline-none"
                    />
                  </div>
                  <div className="flex items-start gap-1.5 rounded-lg border border-ink/20 bg-[#fff9f2] p-2.5 text-[11px] text-muted">
                    <Info className="size-4 shrink-0 text-ink mt-0.5" />
                    <span>Role canonical ID (RL-XXXXXX) will be generated automatically by the backend. Career levels belong to Readiness Engine industry profiles.</span>
                  </div>
                </>
              )}

              {/* SKILLS FORM */}
              {activeTab === "SKILLS" && (
                <>
                  <div>
                    <label className="block text-xs font-bold text-ink">
                      Preferred Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. PyTorch"
                      value={skillForm.preferred_name}
                      onChange={(e) => setSkillForm({ ...skillForm, preferred_name: e.target.value })}
                      required
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs font-bold text-ink focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-ink">
                      Domain / Category <span className="text-muted font-normal">(optional)</span>
                    </label>
                    <select
                      value={skillForm.domain_id}
                      onChange={(e) => setSkillForm({ ...skillForm, domain_id: e.target.value })}
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs font-bold text-ink focus:outline-none"
                    >
                      <option value="">None / Unassigned</option>
                      {domains.map((d) => (
                        <option key={d.domain_id} value={d.domain_id}>
                          {d.name} ({d.code})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-ink">Skill Type</label>
                      <select
                        value={skillForm.skill_type}
                        onChange={(e) => setSkillForm({ ...skillForm, skill_type: e.target.value })}
                        className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs font-bold text-ink focus:outline-none"
                      >
                        <option value="PROGRAMMING_LANGUAGE">Programming Language</option>
                        <option value="PROGRAMMING_SKILL">Programming Skill</option>
                        <option value="SOFTWARE_OR_TOOL">Software / Tool</option>
                        <option value="KNOWLEDGE">Knowledge</option>
                        <option value="OTHER_SKILL">Other Skill</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-ink">Skill Nature</label>
                      <select
                        value={skillForm.skill_nature}
                        onChange={(e) => setSkillForm({ ...skillForm, skill_nature: e.target.value })}
                        className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs font-bold text-ink focus:outline-none"
                      >
                        <option value="TECHNICAL">Technical</option>
                        <option value="BEHAVIOURAL">Behavioural</option>
                        <option value="OTHER">Other</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-ink">Description</label>
                    <textarea
                      placeholder="Description of the skill or competence..."
                      value={skillForm.description}
                      onChange={(e) => setSkillForm({ ...skillForm, description: e.target.value })}
                      rows={2}
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs text-ink focus:outline-none"
                    />
                  </div>
                  <div className="flex items-start gap-1.5 rounded-lg border border-ink/20 bg-[#fff9f2] p-2.5 text-[11px] text-muted">
                    <Info className="size-4 shrink-0 text-ink mt-0.5" />
                    <span>Skill canonical ID (SK-XXXXXX) will be generated automatically by the backend. Aliases are automatically populated via the normalization pipeline.</span>
                  </div>
                </>
              )}

              {/* RELATIONSHIPS FORM */}
              {activeTab === "RELATIONSHIPS" && (
                <>
                  <SkillSearchSelect
                    label="Source Skill"
                    value={relForm.source_skill_id}
                    onChange={(val) => setRelForm({ ...relForm, source_skill_id: val })}
                    skills={skills}
                    placeholder="Search and select source skill..."
                  />

                  <SkillSearchSelect
                    label="Target Skill"
                    value={relForm.target_skill_id}
                    onChange={(val) => setRelForm({ ...relForm, target_skill_id: val })}
                    skills={skills}
                    excludeId={relForm.source_skill_id}
                    placeholder="Search and select target skill..."
                  />

                  <div>
                    <label className="block text-xs font-bold text-ink">
                      Relationship Type <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={relForm.relationship_type}
                      onChange={(e) =>
                        setRelForm({ ...relForm, relationship_type: e.target.value as SkillRelationshipType })
                      }
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs font-bold text-ink focus:outline-none"
                    >
                      <option value="EQUIVALENT_TO">EQUIVALENT_TO (Equivalent meaning)</option>
                      <option value="BROADER_THAN">BROADER_THAN (Broader category/parent)</option>
                      <option value="NARROWER_THAN">NARROWER_THAN (Narrower subcategory/child)</option>
                      <option value="PART_OF">PART_OF (Sub-component of skill)</option>
                      <option value="PREREQUISITE_OF">PREREQUISITE_OF (Required prerequisite)</option>
                      <option value="RELATED_TO">RELATED_TO (General semantic relation)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-ink">Evidence / Justification</label>
                    <textarea
                      placeholder="Ontological evidence note..."
                      value={relForm.evidence_note}
                      onChange={(e) => setRelForm({ ...relForm, evidence_note: e.target.value })}
                      rows={2}
                      className="hard-shadow-sm mt-1 w-full rounded-lg border-2 border-ink bg-[#fff9f2] p-2 text-xs text-ink focus:outline-none"
                    />
                  </div>
                  <div className="flex items-start gap-1.5 rounded-lg border border-ink/20 bg-[#fff9f2] p-2.5 text-[11px] text-muted">
                    <Info className="size-4 shrink-0 text-ink mt-0.5" />
                    <span>Relationship canonical ID (REL-XXXXXX) will be generated automatically by the backend. Duplicate relations are automatically prevented.</span>
                  </div>
                </>
              )}

              <div className="mt-5 flex items-center justify-end gap-2 border-t-2 border-ink/10 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="hard-shadow-sm rounded-lg border-2 border-ink bg-white px-4 py-2 text-xs font-bold text-ink hover:bg-[#fff9f2]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="hard-shadow-sm flex items-center gap-1.5 rounded-lg border-2 border-ink bg-[#d0ffa4] px-4 py-2 text-xs font-black text-ink hover:bg-[#b8f582] disabled:opacity-50"
                >
                  {isSubmitting ? <Loader2 className="size-3.5 animate-spin" /> : <Plus className="size-3.5" />}
                  Submit & Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
