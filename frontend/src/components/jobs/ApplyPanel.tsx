"use client";

import { FileText } from "lucide-react";
import { useActionState, useId, useState } from "react";

import { applyForJob } from "@/app/actions/jobs";

const inputClass =
  "min-h-11 w-full rounded-[10px] border bg-white px-3 py-2.5 text-sm text-[#1d1b24] outline-none focus:border-[#5b3df5] focus:ring-4 focus:ring-[#5b3df5]/15";

type Props = {
  vacancyId: string;
  companyName: string;
  name: string;
  email: string;
  lastCv: { file_name: string; size_bytes: number } | null;
  lastPhone: string | null;
  lastEducation: string | null;
};

/** Apply on Skillaro: the student sees exactly what the company gets, agrees, and sends. */
export function ApplyPanel({ vacancyId, companyName, name, email, lastCv, lastPhone, lastEducation }: Props) {
  const [open, setOpen] = useState(false);
  const [state, action, pending] = useActionState(applyForJob, undefined);
  const [reuse, setReuse] = useState(lastCv !== null);
  const ids = useId();
  const err = state?.errors ?? {};

  if (!open) {
    return (
      <div className="flex flex-wrap items-center gap-3 border-t border-[#efebe3] pt-4">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="inline-flex min-h-11 items-center rounded-xl bg-[#5b3df5] px-[18px] text-sm font-bold text-white shadow-[0_8px_20px_-8px_rgba(91,61,245,0.6)] hover:bg-[#4a2fd0] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30"
        >
          Apply on Skillaro
        </button>
        <span className="text-[13px] leading-normal text-[#5a5663]">You see exactly what {companyName} gets before you send.</span>
      </div>
    );
  }

  const fieldError = (field: string) =>
    err[field] ? (
      <p id={`${ids}-${field}-error`} className="text-[13px] font-medium text-[#c4231b]">
        {err[field]}
      </p>
    ) : null;

  return (
    <form action={action} noValidate className="flex flex-col gap-3.5 border-t border-[#efebe3] pt-4">
      <input type="hidden" name="vacancyId" value={vacancyId} />
      <h3 className="text-lg font-extrabold">Apply to {companyName}</h3>
      {state?.message && (
        <p role="alert" className="rounded-xl border border-[#f5c2d6] bg-[#ffeef5] px-4 py-3 text-sm font-medium text-[#7a1048]">
          {state.message}
        </p>
      )}
      <fieldset className="flex flex-col gap-3 rounded-2xl border border-[#e1d8ff] bg-[#f6f3ff] px-4 py-3.5">
        <legend className="sr-only">What {companyName} will see</legend>
        <p aria-hidden="true" className="text-[13px] font-extrabold text-[#3d24b8]">
          What {companyName} will see
        </p>
        <div className="grid gap-2.5 sm:grid-cols-2">
          <ReadOnly label="Name" value={name} />
          <ReadOnly label="Email" value={email} />
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${ids}-phone`} className="text-[13px] font-bold text-[#3b3845]">
              Phone
            </label>
            <input
              id={`${ids}-phone`}
              name="phone"
              type="tel"
              autoComplete="tel"
              defaultValue={state?.values?.phone ?? lastPhone ?? ""}
              placeholder="077 123 4567"
              aria-invalid={err.phone ? true : undefined}
              aria-describedby={err.phone ? `${ids}-phone-error` : undefined}
              className={`${inputClass} ${err.phone ? "border-[#c4231b]" : "border-[#d9d3c6]"}`}
            />
            {fieldError("phone")}
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${ids}-edu`} className="text-[13px] font-bold text-[#3b3845]">
              Education
            </label>
            <input
              id={`${ids}-edu`}
              name="education"
              maxLength={300}
              defaultValue={state?.values?.education ?? lastEducation ?? ""}
              placeholder="For example: BSc (Hons) in IT, final year"
              className={`${inputClass} border-[#d9d3c6]`}
            />
          </div>
        </div>
        <div className="flex flex-col gap-2 rounded-xl border border-[#e4dfd5] bg-white px-3 py-2.5">
          <span className="flex items-center gap-2 text-[13px] font-bold text-[#3b3845]">
            <FileText className="size-4 text-[#a12626]" aria-hidden="true" />
            Your CV (PDF, up to 2 MB)
          </span>
          {lastCv && (
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input type="checkbox" name="reuseCv" checked={reuse} onChange={(e) => setReuse(e.target.checked)} className="size-[18px] accent-[#5b3df5]" />
              Send the CV from my last application: <strong className="break-all">{lastCv.file_name}</strong>
            </label>
          )}
          <label htmlFor={`${ids}-cv`} className="text-[13px] text-[#5a5663]">
            {lastCv ? "Or choose another PDF:" : "Choose your CV:"}
          </label>
          <input
            id={`${ids}-cv`}
            name="cv"
            type="file"
            accept="application/pdf,.pdf"
            onChange={(e) => {
              if (e.target.files?.length) setReuse(false);
            }}
            aria-invalid={err.cv ? true : undefined}
            aria-describedby={err.cv ? `${ids}-cv-error` : undefined}
            className="text-sm file:mr-3 file:min-h-9 file:cursor-pointer file:rounded-[10px] file:border file:border-[#ddd7cb] file:bg-white file:px-3 file:text-[13px] file:font-bold"
          />
          {fieldError("cv")}
        </div>
      </fieldset>
      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${ids}-note`} className="text-[13px] font-bold text-[#3b3845]">
          Note to the company <span className="font-medium text-[#5a5663]">(optional)</span>
        </label>
        <textarea
          id={`${ids}-note`}
          name="note"
          rows={3}
          maxLength={1000}
          defaultValue={state?.values?.note ?? ""}
          placeholder="A few lines on why this job fits you"
          className={`${inputClass} border-[#d9d3c6] leading-relaxed`}
        />
        {fieldError("note")}
      </div>
      <div className="flex flex-col gap-1">
        <label className="flex cursor-pointer items-start gap-2.5 text-sm leading-normal">
          <input
            type="checkbox"
            name="consent"
            aria-invalid={err.consent ? true : undefined}
            aria-describedby={err.consent ? `${ids}-consent-error` : undefined}
            className="mt-0.5 size-5 shrink-0 accent-[#5b3df5]"
          />
          <span>I agree to share my name, contact details, education, CV and note with {companyName} for this job.</span>
        </label>
        {fieldError("consent")}
      </div>
      <div className="flex flex-wrap items-center gap-2.5">
        <button
          type="submit"
          disabled={pending}
          className="inline-flex min-h-11 items-center rounded-xl bg-[#5b3df5] px-[18px] text-sm font-bold text-white shadow-[0_8px_20px_-8px_rgba(91,61,245,0.6)] hover:bg-[#4a2fd0] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30 disabled:cursor-wait disabled:opacity-70"
        >
          {pending ? "Sending…" : "Send application"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="inline-flex min-h-11 items-center rounded-xl border border-[#ddd7cb] bg-white px-[18px] text-sm font-bold hover:border-[#b9b1a2]"
        >
          Cancel
        </button>
        <span className="text-[13px] text-[#5a5663]">Your skill profile and readiness results are not shared.</span>
      </div>
    </form>
  );
}

function ReadOnly({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[13px] font-bold text-[#3b3845]">
        {label} <span className="font-medium text-[#5a5663]">(from your account)</span>
      </span>
      <span className="flex min-h-11 items-center rounded-[10px] border border-[#e4dfd5] bg-white px-3 text-sm break-all">{value}</span>
    </div>
  );
}
