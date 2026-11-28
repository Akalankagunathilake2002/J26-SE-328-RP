"use client";

import { useEffect, useRef, useState, useTransition } from "react";

import { reviewCompany, setApplicantStatus, setJobStatus, withdrawApplication, type Result } from "@/app/actions/jobs";

const buttonTones = {
  primary: "bg-[#5b3df5] text-white shadow-[0_8px_20px_-8px_rgba(91,61,245,0.6)] hover:bg-[#4a2fd0]",
  ghost: "border border-[#ddd7cb] bg-white text-[#24212c] hover:border-[#b9b1a2]",
  lime: "bg-[#d0ffa4] text-[#1f3a00] hover:bg-[#bff58a]",
  selected: "border border-[#c9b8ff] bg-[#efe8ff] text-[#3d24b8]",
};

/** A button that runs a Server Action, shows that it's working, and shows the action's error under it. */
function ActionButton({
  label,
  pendingLabel,
  run,
  tone = "ghost",
  pressed,
  confirmText,
}: {
  label: string;
  pendingLabel: string;
  run: () => Promise<Result>;
  tone?: keyof typeof buttonTones;
  pressed?: boolean;
  confirmText?: string;
}) {
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);
  return (
    <span className="inline-flex flex-col gap-1">
      <button
        type="button"
        disabled={pending}
        aria-pressed={pressed}
        onClick={() => {
          if (confirmText && !window.confirm(confirmText)) return;
          setError(null);
          start(async () => {
            const result = await run();
            if (result?.error) setError(result.error);
          });
        }}
        className={`inline-flex min-h-9 items-center justify-center rounded-[10px] px-3 text-[13px] font-bold whitespace-nowrap transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#5b3df5]/30 disabled:cursor-wait disabled:opacity-60 ${buttonTones[tone]}`}
      >
        {pending ? pendingLabel : label}
      </button>
      {error && (
        <span role="alert" className="max-w-[260px] text-xs font-medium text-[#c4231b]">
          {error}
        </span>
      )}
    </span>
  );
}

/** Close, publish or reopen one of the company's job posts. */
export function JobStatusButton({ vacancyId, status }: { vacancyId: string; status: "DRAFT" | "PUBLISHED" | "CLOSED" }) {
  if (status === "PUBLISHED") {
    return (
      <ActionButton
        label="Close"
        pendingLabel="Closing…"
        confirmText="Close this job? Students won't see it any more. You keep its applicants."
        run={() => setJobStatus(vacancyId, "CLOSED")}
      />
    );
  }
  return (
    <ActionButton
      label={status === "DRAFT" ? "Publish" : "Reopen"}
      pendingLabel="Publishing…"
      tone="primary"
      run={() => setJobStatus(vacancyId, "PUBLISHED")}
    />
  );
}

export function ApplicantStatusButtons({ applicationId, status, firstName }: { applicationId: string; status: string; firstName: string }) {
  return (
    <div className="flex flex-wrap items-start gap-2.5">
      <ActionButton
        label={status === "SHORTLISTED" ? "Shortlisted" : "Shortlist"}
        pendingLabel="Saving…"
        tone={status === "SHORTLISTED" ? "lime" : "primary"}
        pressed={status === "SHORTLISTED"}
        run={() => (status === "SHORTLISTED" ? Promise.resolve({}) : setApplicantStatus(applicationId, "SHORTLISTED"))}
      />
      <ActionButton
        label="Not selected"
        pendingLabel="Saving…"
        tone={status === "NOT_SELECTED" ? "selected" : "ghost"}
        pressed={status === "NOT_SELECTED"}
        confirmText={status === "NOT_SELECTED" ? undefined : `Mark ${firstName} as not selected? ${firstName} sees this under My applications.`}
        run={() => (status === "NOT_SELECTED" ? Promise.resolve({}) : setApplicantStatus(applicationId, "NOT_SELECTED"))}
      />
    </div>
  );
}

export function CompanyReviewButtons({ companyId, status, name }: { companyId: string; status: string; name: string }) {
  if (status === "REJECTED") {
    return <ActionButton label="Undo" pendingLabel="Undoing…" run={() => reviewCompany(companyId, "reopen")} />;
  }
  if (status === "VERIFIED") {
    return (
      <ActionButton
        label="Remove verification"
        pendingLabel="Saving…"
        confirmText={`Remove ${name}'s verification? Its jobs disappear for students until it is verified again.`}
        run={() => reviewCompany(companyId, "reopen")}
      />
    );
  }
  return (
    <div className="flex flex-wrap items-start gap-2.5">
      <ActionButton label="Verify company" pendingLabel="Verifying…" tone="primary" run={() => reviewCompany(companyId, "verify")} />
      <ActionButton
        label="Reject"
        pendingLabel="Rejecting…"
        confirmText={`Reject ${name}? Its jobs stay hidden from students.`}
        run={() => reviewCompany(companyId, "reject")}
      />
    </div>
  );
}

export function WithdrawButton({ applicationId, small = true }: { applicationId: string; small?: boolean }) {
  return (
    <ActionButton
      label={small ? "Withdraw" : "Withdraw application"}
      pendingLabel="Withdrawing…"
      confirmText="Withdraw this application? The company no longer sees your details."
      run={() => withdrawApplication(applicationId)}
    />
  );
}

/** Marks a new application Seen once the company has opened it (the student sees that), then refreshes the page. */
export function MarkSeen({ applicationId, status }: { applicationId: string; status: string }) {
  const done = useRef<string | null>(null);
  useEffect(() => {
    if (status !== "NEW" || done.current === applicationId) return;
    done.current = applicationId;
    void setApplicantStatus(applicationId, "SEEN");
  }, [applicationId, status]);
  return null;
}
