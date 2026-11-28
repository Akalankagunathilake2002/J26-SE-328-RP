"use client";

import { ScanSearch, X } from "lucide-react";
import Link from "next/link";
import { useId, useState, useTransition } from "react";

import { findJobSkills, saveJob } from "@/app/actions/jobs";
import type { Importance, Job, JobInput, SkillType } from "@/lib/jobs";

type FormSkill = { name: string; skill_type: SkillType; importance: Importance; custom: boolean };

const CAREER_LEVELS = [
  ["INTERN", "Intern"],
  ["TRAINEE", "Trainee"],
  ["JUNIOR", "Junior"],
  ["MID_LEVEL", "Mid level"],
  ["SENIOR", "Senior"],
  ["LEAD", "Lead"],
];
const EMPLOYMENT_TYPES = [
  ["FULL_TIME", "Full time"],
  ["PART_TIME", "Part time"],
  ["CONTRACT", "Contract"],
  ["INTERNSHIP", "Internship"],
];
const EDUCATION = ["G.C.E. O/L", "G.C.E. A/L", "Diploma / HND", "Undergraduate (studying)", "Bachelor's degree", "Master's degree"];

const inputClass =
  "min-h-11 w-full rounded-[10px] border border-[#d9d3c6] bg-white px-3 py-2.5 text-sm text-[#1d1b24] outline-none focus:border-[#5b3df5] focus:ring-4 focus:ring-[#5b3df5]/15";
const labelClass = "text-[13px] font-bold text-[#3b3845]";
const ghostButton =
  "inline-flex min-h-9 items-center justify-center rounded-[10px] border border-[#ddd7cb] bg-white px-3 text-[13px] font-bold text-[#24212c] hover:border-[#b9b1a2] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30";

export function JobForm({
  job,
  skillList,
  companyVerified,
}: {
  job?: Job;
  skillList: { name: string; skill_type: SkillType }[];
  companyVerified: boolean;
}) {
  const known = new Map(skillList.map((s) => [s.name.toLowerCase(), s]));
  const ids = useId();
  const [title, setTitle] = useState(job?.title ?? "");
  const [level, setLevel] = useState(job?.career_level ?? "JUNIOR");
  const [type, setType] = useState(job?.employment_type ?? "FULL_TIME");
  const [location, setLocation] = useState(job?.location ?? "");
  const [closing, setClosing] = useState(job?.closing_date ?? "");
  const [apply, setApply] = useState(job?.apply_url ?? "");
  const [description, setDescription] = useState(job?.description ?? "");
  const [skills, setSkills] = useState<FormSkill[] | null>(
    job ? job.skills.map((s) => ({ ...s, custom: !known.has(s.name.toLowerCase()) })) : null,
  );
  const [education, setEducation] = useState(job?.education ?? "");
  const [years, setYears] = useState(job?.minimum_years != null ? String(job.minimum_years) : "");
  const [certs, setCerts] = useState<string[]>(job?.certifications ?? []);
  const [newSkill, setNewSkill] = useState("");
  const [newCert, setNewCert] = useState("");
  const [notice, setNotice] = useState<{ text: string; error: boolean } | null>(null);
  const [detecting, startDetect] = useTransition();
  const [saving, startSave] = useTransition();
  const [savingAs, setSavingAs] = useState<"DRAFT" | "PUBLISHED" | null>(null);

  const required = (skills ?? []).filter((s) => s.importance === "REQUIRED");
  const preferred = (skills ?? []).filter((s) => s.importance === "PREFERRED");
  const say = (text: string, error = false) => setNotice({ text, error });

  function findSkills() {
    if (description.trim().split(/\s+/).length < 5) {
      say("Write the job description first, then Skillaro can find the skills in it.", true);
      return;
    }
    startDetect(async () => {
      const result = await findJobSkills(title, description);
      if ("error" in result && result.error) {
        say(result.error, true);
        return;
      }
      if (!("skills" in result)) return;
      const found = result.skills.map((s) => ({ name: s.name, skill_type: s.skill_type, importance: s.importance, custom: false }));
      const keep = (skills ?? []).filter((s) => s.custom && !found.some((f) => f.name.toLowerCase() === s.name.toLowerCase()));
      setSkills([...found, ...keep]);
      if (result.education) setEducation(result.education);
      if (result.minimum_years != null) setYears(String(result.minimum_years));
      if (result.certifications.length) setCerts((old) => [...new Set([...old, ...result.certifications])]);
      const req = found.filter((s) => s.importance === "REQUIRED").length;
      say(`Found ${found.length} skills: ${req} required, ${found.length - req} preferred. Check each one, then publish.`);
    });
  }

  function toggle(name: string) {
    setSkills((list) => (list ?? []).map((s) => (s.name === name ? { ...s, importance: s.importance === "REQUIRED" ? "PREFERRED" : "REQUIRED" } : s)));
  }

  function remove(name: string) {
    setSkills((list) => (list ?? []).filter((s) => s.name !== name));
  }

  function addSkill() {
    const raw = newSkill.trim().replace(/\s+/g, " ");
    if (!raw) return;
    const hit = known.get(raw.toLowerCase());
    const name = hit?.name ?? raw;
    if ((skills ?? []).some((s) => s.name.toLowerCase() === name.toLowerCase())) {
      say(`${name} is already in the list.`, true);
      return;
    }
    setSkills([...(skills ?? []), { name, skill_type: hit?.skill_type ?? "TECHNICAL", importance: "REQUIRED", custom: !hit }]);
    setNewSkill("");
    setNotice(null);
  }

  function addCert() {
    const raw = newCert.trim().replace(/\s+/g, " ");
    if (!raw) return;
    if (!certs.some((c) => c.toLowerCase() === raw.toLowerCase())) setCerts([...certs, raw]);
    setNewCert("");
  }

  function save(status: "DRAFT" | "PUBLISHED") {
    if (title.trim().length < 2) {
      say("Add a job title first.", true);
      return;
    }
    if (status === "PUBLISHED" && !skills?.length) {
      say('Press "Find skills in the description" first, so students can see what you need.', true);
      return;
    }
    const input: JobInput = {
      title: title.trim(),
      career_level: level,
      employment_type: type,
      location: location.trim() || null,
      closing_date: closing || null,
      apply_url: apply.trim() || null,
      description,
      status,
      skills: (skills ?? []).map((s) => ({ name: s.name, importance: s.importance, ...(s.custom ? { skill_type: s.skill_type } : {}) })),
      education: education || null,
      minimum_years: years === "" ? null : Math.max(0, Math.min(40, Number(years) || 0)),
      certifications: certs,
    };
    setSavingAs(status);
    startSave(async () => {
      const result = await saveJob(job?.vacancy_id ?? null, input);
      if (result?.error) say(result.error, true);
    });
  }

  const labels =
    job?.status === "PUBLISHED"
      ? { draft: "Move to drafts", publish: "Save changes" }
      : job?.status === "CLOSED"
        ? { draft: "Save, keep closed", publish: "Save and reopen" }
        : { draft: "Save as draft", publish: "Publish job" };

  const skillRow = (s: FormSkill) => (
    <li
      key={s.name}
      className={`flex items-center gap-2 rounded-xl py-2 pr-2 pl-3 ${
        s.importance === "REQUIRED" ? "bg-[#f6f3ff]" : "border border-dashed border-[#c9c2b3] bg-[#fbfaf7]"
      }`}
    >
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="text-sm font-bold">{s.name}</span>
        <span className="text-xs text-[#5a5663]">
          {s.skill_type === "BEHAVIOURAL" ? "Behavioural" : "Technical"}
          {s.custom && " · new, not in the skill list yet"}
        </span>
      </span>
      <button type="button" onClick={() => toggle(s.name)} className={ghostButton}>
        {s.importance === "REQUIRED" ? "Make preferred" : "Make required"}
      </button>
      <button
        type="button"
        onClick={() => remove(s.name)}
        aria-label={`Remove ${s.name}`}
        className="grid size-9 shrink-0 place-items-center rounded-[10px] border border-[#e4dfd5] bg-white text-[#5a5663] hover:border-[#e3b7b7] hover:text-[#842a2a] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30"
      >
        <X className="size-4" aria-hidden="true" />
      </button>
    </li>
  );

  return (
    <div className="flex flex-col gap-4">
      <p aria-live="polite" className="sr-only">
        {notice?.text}
      </p>
      {notice && (
        <p
          className={`rounded-2xl border px-4 py-3 text-sm font-medium ${
            notice.error ? "border-[#f5c2d6] bg-[#ffeef5] text-[#7a1048]" : "border-[#d9cffd] bg-[#f6f3ff] text-[#2c2545]"
          }`}
        >
          {notice.text}
        </p>
      )}
      <div className="flex flex-wrap items-start gap-4">
        <section className="flex min-w-0 flex-[3_1_460px] flex-col gap-3.5 rounded-[18px] border border-[#e4dfd5] bg-white p-5">
          <h2 className="text-[17px] font-extrabold">Job details</h2>
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${ids}-title`} className={labelClass}>
              Job title
            </label>
            <input id={`${ids}-title`} className={inputClass} value={title} maxLength={150} onChange={(e) => setTitle(e.target.value)} placeholder="For example: Junior Software Engineer" />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <label htmlFor={`${ids}-level`} className={labelClass}>
                Career level
              </label>
              <select id={`${ids}-level`} className={inputClass} value={level} onChange={(e) => setLevel(e.target.value)}>
                {CAREER_LEVELS.map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor={`${ids}-type`} className={labelClass}>
                Job type
              </label>
              <select id={`${ids}-type`} className={inputClass} value={type} onChange={(e) => setType(e.target.value)}>
                {EMPLOYMENT_TYPES.map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor={`${ids}-loc`} className={labelClass}>
                Location
              </label>
              <input id={`${ids}-loc`} className={inputClass} value={location} maxLength={120} onChange={(e) => setLocation(e.target.value)} placeholder="For example: Colombo 03 (hybrid)" />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor={`${ids}-close`} className={labelClass}>
                Closing date
              </label>
              <input id={`${ids}-close`} type="date" className={inputClass} value={closing} onChange={(e) => setClosing(e.target.value)} />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${ids}-apply`} className={labelClass}>
              Your own application page <span className="font-medium text-[#5a5663]">(optional)</span>
            </label>
            <input
              id={`${ids}-apply`}
              className={inputClass}
              value={apply}
              maxLength={300}
              onChange={(e) => setApply(e.target.value)}
              placeholder="https://yourcompany.lk/careers or jobs@yourcompany.lk"
              aria-describedby={`${ids}-apply-help`}
            />
            <span id={`${ids}-apply-help`} className="text-xs leading-normal text-[#5a5663]">
              Students apply on Skillaro and you see them under Applicants. If you also use your own form, add its web link or email. Students see it after they apply.
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${ids}-desc`} className={labelClass}>
              Job description
            </label>
            <textarea
              id={`${ids}-desc`}
              rows={14}
              maxLength={8000}
              className={`${inputClass} leading-relaxed`}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={"What the job is, what the person will do, and what you need.\n\nTip: put extras under a heading such as “Nice to have:”, and Skillaro marks those skills Preferred."}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={findSkills}
              disabled={detecting}
              className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-[#d0ffa4] px-[18px] text-sm font-bold text-[#1f3a00] hover:bg-[#bff58a] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30 disabled:cursor-wait disabled:opacity-70"
            >
              <ScanSearch className="size-[18px]" aria-hidden="true" />
              {detecting ? "Finding skills…" : "Find skills in the description"}
            </button>
            <span className="text-[13px] text-[#5a5663]">Uses the same skill list as Market Pulse.</span>
          </div>
        </section>

        <section className="flex min-w-0 flex-[2_1_340px] flex-col gap-3.5 rounded-[18px] border border-[#e4dfd5] bg-white p-5">
          <h2 className="text-[17px] font-extrabold">Skills students need</h2>
          {skills === null ? (
            <p className="rounded-2xl border border-dashed border-[#c9c2b3] bg-[#fbfaf7] p-4 text-sm leading-relaxed text-[#3b3845]">
              No skills yet. Write the description and press <strong>Find skills in the description</strong>. Then mark each skill Required or Preferred, remove any that don&apos;t fit, or add your own.
            </p>
          ) : (
            <div className="flex flex-col gap-3.5">
              <SkillGroup title="Required" count={required.length} empty="No required skills.">
                {required.map(skillRow)}
              </SkillGroup>
              <SkillGroup title="Preferred" count={preferred.length} empty="No preferred skills." dashed>
                {preferred.map(skillRow)}
              </SkillGroup>
            </div>
          )}
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${ids}-new`} className={labelClass}>
              Add a skill the description doesn&apos;t mention
            </label>
            <div className="flex gap-2">
              <input
                id={`${ids}-new`}
                list={`${ids}-skills`}
                className={inputClass}
                value={newSkill}
                maxLength={80}
                onChange={(e) => setNewSkill(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addSkill();
                  }
                }}
                placeholder="For example: Figma"
              />
              <datalist id={`${ids}-skills`}>
                {skillList.map((s) => (
                  <option key={s.name} value={s.name} />
                ))}
              </datalist>
              <button type="button" onClick={addSkill} className={`${ghostButton} min-h-11 px-4`}>
                Add
              </button>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <label htmlFor={`${ids}-edu`} className={labelClass}>
                Education
              </label>
              <select id={`${ids}-edu`} className={inputClass} value={education} onChange={(e) => setEducation(e.target.value)}>
                <option value="">Not needed</option>
                {EDUCATION.map((e) => (
                  <option key={e} value={e}>
                    {e}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor={`${ids}-years`} className={labelClass}>
                Minimum experience (years)
              </label>
              <input id={`${ids}-years`} type="number" min={0} max={40} className={inputClass} value={years} onChange={(e) => setYears(e.target.value)} />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${ids}-cert`} className={labelClass}>
              Certificates and licences <span className="font-medium text-[#5a5663]">(optional)</span>
            </label>
            {certs.length > 0 && (
              <ul className="flex flex-wrap gap-1.5">
                {certs.map((c) => (
                  <li key={c} className="inline-flex items-center gap-1 rounded-full bg-[#f4f2ee] py-1 pr-1 pl-2.5 text-[12.5px] font-semibold">
                    {c}
                    <button type="button" onClick={() => setCerts(certs.filter((x) => x !== c))} aria-label={`Remove ${c}`} className="grid size-6 place-items-center rounded-full hover:bg-[#e4dfd5]">
                      <X className="size-3.5" aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div className="flex gap-2">
              <input
                id={`${ids}-cert`}
                className={inputClass}
                value={newCert}
                maxLength={120}
                onChange={(e) => setNewCert(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addCert();
                  }
                }}
                placeholder="For example: Driving licence"
              />
              <button type="button" onClick={addCert} className={`${ghostButton} min-h-11 px-4`}>
                Add
              </button>
            </div>
          </div>
          <div className="flex flex-col gap-2.5 border-t border-[#efebe3] pt-3.5">
            {!companyVerified && (
              <p className="text-[13px] leading-normal text-[#5a5663]">Your company isn&apos;t verified yet, so students will see this job after verification.</p>
            )}
            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                disabled={saving}
                onClick={() => save("DRAFT")}
                className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#ddd7cb] bg-white px-3 text-sm font-bold hover:border-[#b9b1a2] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30 disabled:cursor-wait disabled:opacity-60"
              >
                {saving && savingAs === "DRAFT" ? "Saving…" : labels.draft}
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={() => save("PUBLISHED")}
                className="inline-flex min-h-11 items-center justify-center rounded-xl bg-[#5b3df5] px-3 text-sm font-bold text-white shadow-[0_8px_20px_-8px_rgba(91,61,245,0.6)] hover:bg-[#4a2fd0] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30 disabled:cursor-wait disabled:opacity-60"
              >
                {saving && savingAs === "PUBLISHED" ? "Publishing…" : labels.publish}
              </button>
            </div>
            {job && (
              <Link href="/company" className="text-center text-[13px] font-semibold text-[#4a2fd0] underline underline-offset-4">
                Cancel
              </Link>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function SkillGroup({ title, count, empty, dashed, children }: { title: string; count: number; empty: string; dashed?: boolean; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-2">
        <span className="text-sm font-extrabold">{title}</span>
        <span
          className={`rounded-full px-2.5 py-0.5 text-[12.5px] font-semibold ${
            dashed ? "border border-dashed border-[#a39b8b] bg-white text-[#46433c]" : "bg-[#efe8ff] text-[#3d24b8]"
          }`}
        >
          {count}
        </span>
      </div>
      {count === 0 ? <p className="text-[13px] text-[#5a5663]">{empty}</p> : <ul className="flex flex-col gap-1.5">{children}</ul>}
    </div>
  );
}
