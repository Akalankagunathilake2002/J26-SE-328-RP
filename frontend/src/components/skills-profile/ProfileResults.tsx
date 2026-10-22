"use client";

import { useMemo, useState } from "react";
import { Award, ChevronDown, FileText, Layers, Search, Sparkles } from "lucide-react";

import {
  EVIDENCE_LABELS,
  SOURCE_LABELS,
  type ConfidenceLevel,
  type ProfileSkill,
  type SourceType,
  type SkillProfile,
} from "@/lib/profileApi";

const LEVEL_STYLE: Record<ConfidenceLevel, { chip: string; bar: string }> = {
  strong: { chip: "bg-lime", bar: "bg-[#1f8a4c]" },
  moderate: { chip: "bg-sun", bar: "bg-[#c27a00]" },
  weak: { chip: "bg-white text-muted", bar: "bg-[#9a9a90]" },
};

const SOURCE_STYLE: Record<SourceType, string> = {
  cv: "bg-[#b4c2fe]",
  project_description: "bg-peach",
  academic_document: "bg-lavender",
  certificate: "bg-sun",
  portfolio_link: "bg-pink",
};

// How a wording was linked to its standard skill name, in everyday words
const MATCH_LABELS: Record<string, { label: string; style: string; hint: string }> = {
  exact: { label: "Same skill", style: "bg-lime", hint: "a common other name for this skill" },
  cleaned: { label: "Tidied up", style: "bg-cyan", hint: "version numbers or extra letters removed" },
  fuzzy: { label: "Spelling fixed", style: "bg-sun", hint: "a small typo was corrected" },
  semantic: { label: "Same meaning", style: "bg-lavender", hint: "different words, same skill" },
};

// The kinds of proof from strongest to weakest, as the score counts them
const PROOF_ORDER = [
  { label: "Certificate or GitHub code", note: "someone else can check it" },
  { label: "Project or internship report", note: "a separate document about your work" },
  { label: "Studied it (transcript, modules)", note: "learned in a course" },
  { label: "Used it in a CV project or job", note: "you describe doing something" },
  { label: "Listed in your CV", note: "named, without more detail" },
  { label: "Only an interest", note: "“interested in”, “learning”" },
];

const LEVELS: (ConfidenceLevel | "all")[] = ["all", "strong", "moderate", "weak"];

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

// Results of one profile build: summary, detected documents, skills with proof, and the AI steps
export function ProfileResults({ profile }: { profile: SkillProfile }) {
  const [tab, setTab] = useState<"skills" | "analysis">("skills");
  const [level, setLevel] = useState<ConfidenceLevel | "all">("all");

  const counts = useMemo(() => {
    const result = { strong: 0, moderate: 0, weak: 0 };
    profile.skills.forEach((skill) => (result[skill.confidence_level] += 1));
    return result;
  }, [profile]);

  const shown = profile.skills.filter((skill) => level === "all" || skill.confidence_level === level);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border-2 border-ink bg-white p-5 shadow-[4px_4px_0px_#000] sm:p-6">
        <div className="mb-4 flex items-center gap-2">
          <Award className="size-5" />
          <h2 className="text-lg font-extrabold sm:text-xl">Your profile</h2>
        </div>
        <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-4">
          {[
            { label: "Skills found", value: profile.skills.length, color: "bg-[#b4c2fe]" },
            { label: "Strong", value: counts.strong, color: "bg-lime" },
            { label: "Moderate", value: counts.moderate, color: "bg-sun" },
            { label: "Weak", value: counts.weak, color: "bg-[#fff6ea]" },
          ].map((card) => (
            <div key={card.label} className={`${card.color} rounded-xl border-2 border-ink p-4 shadow-[3px_3px_0px_#000]`}>
              <span className="text-xs font-bold">{card.label}</span>
              <p className="mt-2 text-3xl font-black tabular-nums">{card.value}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-[13px] text-muted">
          Strong ≥ 70% · Moderate 40–69% · Weak &lt; 40%. Weak means there is not enough proof yet, not that you
          lack the skill. Add a project report, certificate or GitHub link to raise it.
        </p>

        <h3 className="mt-6 flex items-center gap-2 font-extrabold">
          <FileText className="size-4" /> Documents ({profile.documents.length})
        </h3>
        <ul className="mt-3 grid gap-2 sm:grid-cols-2">
          {profile.documents.map((document) => (
            <li key={document.name} className="rounded-lg border-2 border-ink bg-cream px-3 py-2 text-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-semibold">{document.name}</span>
                <span
                  className={`${SOURCE_STYLE[document.source_type]} shrink-0 rounded-md border-2 border-ink px-2 py-0.5 text-[11px] font-bold uppercase`}
                >
                  {SOURCE_LABELS[document.source_type]}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted">
                {document.skill_count} skills ·{" "}
                {document.type_detected_by === "structure"
                  ? "type detected from its CV sections"
                  : document.type_detected_by === "wording"
                    ? "type detected from its certificate wording"
                    : document.type_detected_by === "layout"
                      ? "type detected from its layout (little text with a date)"
                      : document.type_detected_by === "github"
                        ? "read from GitHub"
                        : `type detected by meaning (similarity ${document.type_confidence?.toFixed(2) ?? "–"})`}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <div className="flex gap-2" role="tablist" aria-label="Profile views">
        {[
          { id: "skills" as const, label: "Skills", icon: Layers },
          { id: "analysis" as const, label: "AI analysis", icon: Sparkles },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            onClick={() => setTab(id)}
            className={`inline-flex items-center gap-2 rounded-xl border-2 border-ink px-4 py-2 text-sm font-bold shadow-[3px_3px_0px_#000] ${
              tab === id ? "bg-pink" : "bg-white"
            }`}
          >
            <Icon className="size-4" /> {label}
          </button>
        ))}
      </div>

      {tab === "skills" ? (
        <section className="rounded-2xl border-2 border-ink bg-white p-5 shadow-[4px_4px_0px_#000] sm:p-6">
          <div className="mb-3 flex flex-wrap gap-1.5 border-b-2 border-ink pb-3">
            {LEVELS.map((value) => (
              <button
                key={value}
                type="button"
                aria-pressed={level === value}
                onClick={() => setLevel(value)}
                className={`rounded-lg px-3 py-1 text-sm font-bold capitalize ${
                  level === value ? "border-2 border-ink bg-lime" : "border-2 border-transparent text-muted"
                }`}
              >
                {value === "all" ? `All (${profile.skills.length})` : `${value} (${counts[value]})`}
              </button>
            ))}
          </div>
          {shown.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted">No skills at this level.</p>
          ) : (
            <ul>
              {shown.map((skill) => (
                <SkillRow key={skill.skill_id} skill={skill} />
              ))}
            </ul>
          )}
        </section>
      ) : (
        <AnalysisView profile={profile} />
      )}
    </div>
  );
}

function SkillRow({ skill }: { skill: ProfileSkill }) {
  const style = LEVEL_STYLE[skill.confidence_level];
  return (
    <li className="border-b border-ink/15 last:border-b-0">
      <details className="group">
        <summary className="grid cursor-pointer list-none grid-cols-[minmax(0,1fr)_56px] items-center gap-3 py-3 sm:grid-cols-[minmax(0,1.4fr)_minmax(90px,1fr)_56px_96px]">
          <span className="min-w-0">
            <span className="flex items-center gap-1.5 font-bold">
              <ChevronDown className="size-4 shrink-0 transition-transform group-open:rotate-180" />
              <span className="truncate">{skill.name}</span>
            </span>
            <span className="ml-5 block text-xs text-muted">
              {skill.documents.length} document{skill.documents.length > 1 ? "s" : ""} · {skill.evidence.length} kind
              {skill.evidence.length > 1 ? "s" : ""} of proof
            </span>
          </span>
          <span className="col-span-2 h-3 rounded-full border-2 border-ink bg-page sm:col-span-1">
            <span className={`block h-full rounded-full ${style.bar}`} style={{ width: percent(skill.confidence) }} />
          </span>
          <span className="row-start-1 text-right font-black tabular-nums sm:row-start-auto">
            {percent(skill.confidence)}
          </span>
          <span
            className={`${style.chip} col-span-2 justify-self-start rounded-md border-2 border-ink px-2 py-0.5 text-center text-[11px] font-bold uppercase sm:col-span-1 sm:justify-self-stretch`}
          >
            {skill.confidence_level}
          </span>
        </summary>

        <div className="mb-3 ml-5 space-y-2 rounded-xl border-2 border-ink bg-cream p-3 text-sm">
          <div className="flex flex-wrap gap-1.5">
            {skill.evidence.map((item) => (
              <span
                key={`${item.source}-${item.evidence_type}`}
                className={`${SOURCE_STYLE[item.source]} rounded-md border-2 border-ink px-2 py-0.5 text-xs font-bold`}
              >
                {SOURCE_LABELS[item.source]}: {EVIDENCE_LABELS[item.evidence_type]}
                {item.mentions > 1 ? ` ×${item.mentions}` : ""} · {percent(item.strength)}
              </span>
            ))}
          </div>
          <ul className="space-y-1.5">
            {skill.mentions.slice(0, 6).map((mention, index) => (
              <li key={index} className="text-[13px]">
                <span className="font-semibold">“{mention.matched_text}”</span>
                <span className="text-muted"> · {mention.sentence}</span>
              </li>
            ))}
          </ul>
        </div>
      </details>
    </li>
  );
}

function plural(count: number, word: string) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

// The build explained for the user in everyday words, with this profile's own numbers
function AnalysisView({ profile }: { profile: SkillProfile }) {
  const mentions = profile.skills.flatMap((skill) => skill.mentions);
  const matched = useMemo(() => {
    const seen = new Map<string, { written: string; skill: string; how: string }>();
    profile.skills.forEach((skill) =>
      skill.mentions.forEach((mention) => {
        const key = `${mention.matched_text.toLowerCase()}|${skill.skill_id}`;
        if (!seen.has(key) && mention.matched_text.toLowerCase() !== skill.name.toLowerCase()) {
          seen.set(key, { written: mention.matched_text, skill: skill.name, how: mention.match_method });
        }
      }),
    );
    return [...seen.values()].slice(0, 15);
  }, [profile]);

  const documentKinds = Object.entries(
    profile.documents.reduce<Record<string, number>>((kinds, document) => {
      const label = SOURCE_LABELS[document.source_type];
      kinds[label] = (kinds[label] ?? 0) + 1;
      return kinds;
    }, {}),
  )
    .map(([label, count]) => `${count} ${label.toLowerCase()}`)
    .join(", ");
  const levels = { strong: 0, moderate: 0, weak: 0 };
  profile.skills.forEach((skill) => (levels[skill.confidence_level] += 1));
  const usedInWork = profile.skills.filter((skill) =>
    skill.evidence.some((proof) => proof.evidence_type === "project_demonstrated"),
  ).length;

  const steps = [
    {
      title: `We read your ${plural(profile.documents.length, "document")}`,
      detail: `We found ${documentKinds || "no documents"}. We work out each document's type ourselves, so you never have to label them.`,
    },
    {
      title: `We found ${plural(mentions.length, "skill mention")}`,
      detail: "We looked through every sentence for skills, using a list of 1,853 recognised skills.",
    },
    {
      title: "We matched your wording to standard skill names",
      detail:
        matched.length > 0
          ? `${plural(matched.length, "wording")} became a standard name, so the same skill is always counted once (see the right).`
          : "You used the standard names already, so nothing needed changing.",
    },
    {
      title: "We checked how you used each skill",
      detail: `Doing something with a skill counts more than just listing it. ${plural(usedInWork, "skill")} showed real use in work or projects.`,
    },
    {
      title: `We scored your ${plural(profile.skills.length, "skill")}`,
      detail: `More proof, and stronger proof, gives a higher score: ${levels.strong} strong, ${levels.moderate} moderate, ${levels.weak} weak.`,
    },
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="rounded-2xl border-2 border-ink bg-white p-5 shadow-[4px_4px_0px_#000]">
        <h2 className="text-lg font-extrabold">How we built your profile</h2>
        <p className="mt-1 text-sm text-muted">Five steps, from your documents to your scores.</p>
        <ol className="mt-4 space-y-3">
          {steps.map((step, index) => (
            <li key={step.title} className="grid grid-cols-[30px_minmax(0,1fr)] gap-3">
              <span className="grid size-7 place-items-center rounded-full border-2 border-ink bg-sun text-sm font-black">
                {index + 1}
              </span>
              <span>
                <span className="block font-bold">{step.title}</span>
                <span className="block text-[13px] text-muted">{step.detail}</span>
              </span>
            </li>
          ))}
        </ol>

        <div className="mt-5 rounded-xl border-2 border-ink bg-cream p-4">
          <h3 className="font-extrabold">Which proof counts most?</h3>
          <p className="text-[13px] text-muted">From strongest to weakest:</p>
          <ol className="mt-2 space-y-1.5 text-[13px]">
            {PROOF_ORDER.map((proof, index) => (
              <li key={proof.label} className="flex items-center gap-2">
                <span
                  className="h-2.5 shrink-0 rounded-full bg-[#1f8a4c]"
                  style={{ width: `${48 - index * 7}px`, opacity: 1 - index * 0.13 }}
                />
                <span>
                  <span className="font-semibold">{proof.label}</span>
                  <span className="text-muted"> · {proof.note}</span>
                </span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="rounded-2xl border-2 border-ink bg-white p-5 shadow-[4px_4px_0px_#000]">
        <h2 className="flex items-center gap-2 text-lg font-extrabold">
          <Search className="size-5" /> Your words, our skill names
        </h2>
        <p className="mt-1 text-sm text-muted">
          People write the same skill in different ways. We give each one a standard name, so employers and the rest of
          Skillaro understand it the same way.
        </p>
        {matched.length === 0 ? (
          <p className="mt-4 rounded-xl border-2 border-dashed border-ink/40 p-4 text-sm text-muted">
            Every skill was already written with its standard name.
          </p>
        ) : (
          <ul className="mt-4 space-y-2">
            {matched.map((row) => {
              const how = MATCH_LABELS[row.how] ?? MATCH_LABELS.semantic;
              return (
                <li
                  key={`${row.written}-${row.skill}`}
                  className="rounded-xl border-2 border-ink/20 px-3 py-2.5 text-[13px]"
                >
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <span className="rounded-md bg-page px-2 py-0.5">&ldquo;{row.written}&rdquo;</span>
                    <span aria-hidden>→</span>
                    <span className="font-bold">{row.skill}</span>
                    <span className={`ml-auto rounded-full border-2 border-ink px-2 text-[11px] font-bold ${how.style}`}>
                      {how.label}
                    </span>
                  </div>
                  <p className="mt-1 text-[12px] text-muted">{how.hint}</p>
                </li>
              );
            })}
          </ul>
        )}

        {profile.unlinked.length > 0 && (
          <>
            <h3 className="mt-5 font-extrabold">Noticed, but not matched yet ({profile.unlinked.length})</h3>
            <p className="text-[13px] text-muted">
              These look like skills, but they are not in our skill list yet, so they are not scored.
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {[...new Set(profile.unlinked.map((span) => span.text))].slice(0, 20).map((text) => (
                <span key={text} className="rounded-full border-2 border-ink bg-page px-2.5 py-0.5 text-xs font-semibold">
                  {text}
                </span>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
