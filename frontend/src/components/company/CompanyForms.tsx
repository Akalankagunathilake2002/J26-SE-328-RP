"use client";

import Link from "next/link";
import { useActionState } from "react";

import { createCompanyProfile, registerCompany, updateCompanyProfile, type FormState } from "@/app/actions/jobs";

const SECTORS = ["IT", "HR", "Management", "Agriculture", "Other"];

const inputClass =
  "min-h-11 w-full rounded-[10px] border bg-white px-3 py-2.5 text-[15px] text-[#1d1b24] outline-none transition-[border-color,box-shadow] focus:border-[#5b3df5] focus:ring-4 focus:ring-[#5b3df5]/15";

type FieldProps = {
  label: string;
  name: string;
  state: FormState;
  type?: string;
  autoComplete?: string;
  defaultValue?: string | null;
  placeholder?: string;
  hint?: string;
};

export function TextField({ label, name, state, type = "text", autoComplete, defaultValue, placeholder, hint }: FieldProps) {
  const error = state?.errors?.[name];
  const describedBy = error ? `${name}-error` : hint ? `${name}-hint` : undefined;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={name} className="text-[13px] font-bold text-[#3b3845]">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        autoComplete={autoComplete}
        placeholder={placeholder}
        defaultValue={state?.values?.[name] ?? defaultValue ?? undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`${inputClass} ${error ? "border-[#c4231b]" : "border-[#d9d3c6]"}`}
      />
      {error ? (
        <p id={`${name}-error`} className="text-[13px] font-medium text-[#c4231b]">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${name}-hint`} className="text-[12.5px] text-[#5a5663]">
            {hint}
          </p>
        )
      )}
    </div>
  );
}

function SectorField({ state, defaultValue }: { state: FormState; defaultValue?: string | null }) {
  const error = state?.errors?.sector;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor="sector" className="text-[13px] font-bold text-[#3b3845]">
        Sector
      </label>
      <select
        id="sector"
        name="sector"
        defaultValue={state?.values?.sector ?? defaultValue ?? "IT"}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? "sector-error" : undefined}
        className={`${inputClass} ${error ? "border-[#c4231b]" : "border-[#d9d3c6]"}`}
      >
        {SECTORS.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
      {error && (
        <p id="sector-error" className="text-[13px] font-medium text-[#c4231b]">
          {error}
        </p>
      )}
    </div>
  );
}

export function FormMessage({ state }: { state: FormState }) {
  if (!state?.message) return null;
  return (
    <p role="alert" className="rounded-xl border border-[#f5c2d6] bg-[#ffeef5] px-4 py-3 text-[14px] font-medium text-[#7a1048]">
      {state.message}
    </p>
  );
}

export function SubmitButton({ pending, label, pendingLabel }: { pending: boolean; label: string; pendingLabel: string }) {
  return (
    <button
      type="submit"
      disabled={pending}
      className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-[#5b3df5] px-5 text-[15px] font-bold text-white shadow-[0_8px_20px_-8px_rgba(91,61,245,0.6)] transition hover:bg-[#4a2fd0] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30 disabled:cursor-wait disabled:opacity-70"
    >
      {pending ? pendingLabel : label}
    </button>
  );
}

/** Company sign-up: the person's account (role hr) and the company, in one form. */
export function CompanyRegisterForm() {
  const [state, action, pending] = useActionState(registerCompany, undefined);
  return (
    <form action={action} noValidate className="flex flex-col gap-3.5">
      <FormMessage state={state} />
      <TextField label="Company name" name="companyName" state={state} autoComplete="organization" />
      <div className="grid gap-3 sm:grid-cols-2">
        <TextField label="Website" name="website" state={state} autoComplete="url" placeholder="yourcompany.lk" />
        <SectorField state={state} />
        <TextField label="Main office city" name="city" state={state} autoComplete="address-level2" />
        <TextField label="Your name" name="fullName" state={state} autoComplete="name" />
      </div>
      <TextField label="Work email" name="email" type="email" state={state} autoComplete="email" hint="Use your company's email domain, so an admin can verify you quickly." />
      <TextField label="Password" name="password" type="password" state={state} autoComplete="new-password" placeholder="At least 8 characters" />
      <SubmitButton pending={pending} label="Create company account" pendingLabel="Creating account…" />
      <p className="text-center text-[13px] text-[#5a5663]">
        Already registered?{" "}
        <Link href="/login" className="font-semibold text-[#4a2fd0] underline underline-offset-4">
          Log in
        </Link>
        . Companies and students use the same Log in page.
      </p>
    </form>
  );
}

type CompanyValues = { name: string; website: string | null; sector: string | null; city: string | null; description: string | null };

/** The company's details: create them (a company account without a company yet) or change them. */
export function CompanyDetailsForm({ company }: { company?: CompanyValues }) {
  const [state, action, pending] = useActionState(company ? updateCompanyProfile : createCompanyProfile, undefined);
  return (
    <form action={action} noValidate className="flex flex-col gap-3.5">
      <FormMessage state={state} />
      {state?.saved && (
        <p role="status" className="rounded-xl border border-[#bfe8cb] bg-[#eefbf1] px-4 py-3 text-[14px] font-medium text-[#123d22]">
          Saved.
        </p>
      )}
      <TextField label="Company name" name="companyName" state={state} defaultValue={company?.name} autoComplete="organization" />
      <div className="grid gap-3 sm:grid-cols-3">
        <TextField label="Website" name="website" state={state} defaultValue={company?.website} placeholder="yourcompany.lk" />
        <SectorField state={state} defaultValue={company?.sector} />
        <TextField label="Main office city" name="city" state={state} defaultValue={company?.city} />
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor="description" className="text-[13px] font-bold text-[#3b3845]">
          About the company <span className="font-medium text-[#5a5663]">(optional)</span>
        </label>
        <textarea
          id="description"
          name="description"
          rows={4}
          maxLength={1000}
          defaultValue={state?.values?.description ?? company?.description ?? ""}
          className={`${inputClass} border-[#d9d3c6] leading-relaxed`}
        />
      </div>
      <div className="sm:max-w-[260px]">
        <SubmitButton pending={pending} label={company ? "Save changes" : "Save company"} pendingLabel="Saving…" />
      </div>
    </form>
  );
}
