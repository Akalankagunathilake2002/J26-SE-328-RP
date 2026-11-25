"use client";

import { useActionState } from "react";

import { login, register, type AuthFormState } from "@/app/actions/auth";
import { ArrowRightIcon } from "@/components/icons";

export function LoginForm({ next }: { next: string }) {
  const [state, action, pending] = useActionState(login, undefined);

  return (
    <form action={action} noValidate className="flex flex-col gap-5">
      <input type="hidden" name="next" value={next} />
      <FormMessage state={state} />
      <Field label="Email" name="email" type="email" autoComplete="email" defaultValue={state?.values?.email} error={state?.errors?.email} />
      <Field label="Password" name="password" type="password" autoComplete="current-password" error={state?.errors?.password} />
      <SubmitButton pending={pending} label="Log in" pendingLabel="Logging in…" />
    </form>
  );
}

export function RegisterForm({ next }: { next: string }) {
  const [state, action, pending] = useActionState(register, undefined);

  return (
    <form action={action} noValidate className="flex flex-col gap-5">
      <input type="hidden" name="next" value={next} />
      <FormMessage state={state} />
      <Field label="Full name" name="fullName" autoComplete="name" defaultValue={state?.values?.fullName} error={state?.errors?.fullName} />
      <Field label="Email" name="email" type="email" autoComplete="email" defaultValue={state?.values?.email} error={state?.errors?.email} />
      <Field label="Password" name="password" type="password" autoComplete="new-password" hint="At least 8 characters." error={state?.errors?.password} />
      <Field label="Confirm password" name="confirmPassword" type="password" autoComplete="new-password" error={state?.errors?.confirmPassword} />
      <SubmitButton pending={pending} label="Create account" pendingLabel="Creating account…" />
    </form>
  );
}

type FieldProps = {
  label: string;
  name: string;
  type?: string;
  autoComplete?: string;
  defaultValue?: string;
  hint?: string;
  error?: string;
};

function Field({ label, name, type = "text", autoComplete, defaultValue, hint, error }: FieldProps) {
  const describedBy = error ? `${name}-error` : hint ? `${name}-hint` : undefined;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={name} className="text-[15px] font-semibold">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        autoComplete={autoComplete}
        defaultValue={defaultValue}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`h-12 rounded-xl border bg-[#faf9f6] px-4 text-[16px] outline-none transition-[border-color,box-shadow,background-color] focus:bg-white focus:ring-4 ${error ? "border-[#c4231b] focus:ring-[#c4231b]/15" : "border-[#e4dfd5] focus:border-[#6d4aff] focus:ring-[#6d4aff]/15"}`}
      />
      {error ? (
        <p id={`${name}-error`} className="text-[14px] font-medium text-[#c4231b]">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${name}-hint`} className="text-[14px] text-muted">
            {hint}
          </p>
        )
      )}
    </div>
  );
}

function FormMessage({ state }: { state: AuthFormState }) {
  if (!state?.message) return null;
  return (
    <p role="alert" className="rounded-xl border border-[#f5c2d6] bg-[#ffeef5] px-4 py-3 text-[15px] font-medium text-[#7a1048]">
      {state.message}
    </p>
  );
}

function SubmitButton({ pending, label, pendingLabel }: { pending: boolean; label: string; pendingLabel: string }) {
  return (
    <button
      type="submit"
      disabled={pending}
      className="mt-2 inline-flex h-14 items-center justify-center gap-3 rounded-full bg-[#6d4aff] text-[17px] font-bold text-white shadow-[0_14px_30px_-12px_rgba(109,74,255,0.9)] transition hover:-translate-y-0.5 hover:bg-[#5f3cf5] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#6d4aff]/30 disabled:cursor-wait disabled:opacity-70 disabled:hover:translate-y-0"
    >
      {pending ? pendingLabel : label}
      {!pending && <ArrowRightIcon className="size-5" />}
    </button>
  );
}
