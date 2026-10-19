"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import { Check, Loader2 } from "lucide-react";

export const ASSESSMENT_STEPS = [
  "Understanding your current strengths",
  "Reviewing industry expectations",
  "Measuring your role alignment",
  "Identifying important skill gaps",
  "Calculating your readiness score",
  "Preparing your career insights",
] as const;

// Progression percentage corresponding to each step
const STEP_PERCENTAGES = [15, 30, 45, 60, 75, 90, 100];

const emptySubscribe = () => () => {};

export interface CareerReadinessLoadingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
  // Optional parameters for future backend API integration
  activeStepOverride?: number;
  isApiDriven?: boolean;
}

// Reusable modal presenting the six-step assessment generation progression
export function CareerReadinessLoadingModal({
  isOpen,
  onClose,
  onComplete,
  activeStepOverride,
  isApiDriven = false,
}: CareerReadinessLoadingModalProps) {
  const isClient = useSyncExternalStore(emptySubscribe, () => true, () => false);
  const [prevIsOpen, setPrevIsOpen] = useState(false);
  // Current active step index (0 to 5 for active steps, 6 when all are complete)
  const [internalStepIndex, setInternalStepIndex] = useState(0);

  // Directly derive active step in API-driven mode without setting state in an effect
  const currentStepIndex =
    isApiDriven && typeof activeStepOverride === "number"
      ? activeStepOverride
      : internalStepIndex;

  // Reset to step 0 during render when the modal opens without triggering cascading renders
  if (isOpen !== prevIsOpen) {
    setPrevIsOpen(isOpen);
    if (isOpen) {
      setInternalStepIndex(0);
    }
  }

  // Manage body scroll lock and escape key handler
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }

    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Simulate 1-second step advancement in static demo mode
  useEffect(() => {
    if (!isOpen || isApiDriven) {
      return;
    }

    let completionTimer: ReturnType<typeof setTimeout> | undefined;

    const intervalTimer = setInterval(() => {
      setInternalStepIndex((prevIndex) => {
        const nextIndex = prevIndex + 1;

        // When all 6 steps complete, clear interval and trigger onComplete
        if (nextIndex >= ASSESSMENT_STEPS.length) {
          clearInterval(intervalTimer);

          completionTimer = setTimeout(() => {
            onComplete?.();
          }, 500);

          return ASSESSMENT_STEPS.length;
        }

        return nextIndex;
      });
    }, 1000);

    return () => {
      clearInterval(intervalTimer);
      if (completionTimer) {
        clearTimeout(completionTimer);
      }
    };
  }, [isOpen, isApiDriven, onComplete]);

  if (!isOpen || !isClient) {
    return null;
  }

  const percentage = STEP_PERCENTAGES[currentStepIndex] ?? 100;
  const displayStepNumber = Math.min(currentStepIndex + 1, ASSESSMENT_STEPS.length);

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="career-readiness-loading-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      {/* Modal Dialog Card */}
      <div
        className="relative w-full max-w-[380px] sm:max-w-[410px] bg-[#fbf2e5] border-2 sm:border-[2.5px] border-ink rounded-3xl p-5 sm:p-6 shadow-[6px_6px_0px_#000] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Title and Description */}
        <div>
          <h3
            id="career-readiness-loading-title"
            className="font-black text-lg sm:text-xl text-ink tracking-tight leading-snug"
          >
            Creating your readiness assessment...
          </h3>
          <p className="text-xs text-ink/75 font-semibold mt-1 leading-snug">
            We are analyzing your profile data. This will take a moment.
          </p>
        </div>

        {/* Strong Black Divider */}
        <div className="h-[2px] bg-ink w-full my-3 sm:my-3.5" />

        {/* 6 Vertically Stacked Steps */}
        <div className="flex flex-col gap-2.5 sm:gap-3 my-0.5">
          {ASSESSMENT_STEPS.map((stepLabel, index) => {
            const isCompleted = index < currentStepIndex;
            const isActive = index === currentStepIndex && currentStepIndex < ASSESSMENT_STEPS.length;

            return (
              <div key={stepLabel} className="flex items-center gap-2.5 sm:gap-3">
                {/* Status Icon Indicator */}
                {isCompleted ? (
                  <span className="size-6 sm:size-6.5 rounded-full bg-lime border-2 border-ink flex items-center justify-center shrink-0 shadow-[1px_1px_0px_#000]">
                    <Check className="size-3.5 text-ink stroke-[3]" />
                  </span>
                ) : isActive ? (
                  <span className="size-6 sm:size-6.5 rounded-full bg-[#006ee9] border-2 border-ink flex items-center justify-center shrink-0 shadow-[1px_1px_0px_#000]">
                    <Loader2 className="size-3.5 text-white animate-spin stroke-[2.5]" />
                  </span>
                ) : (
                  <span className="size-6 sm:size-6.5 rounded-full bg-white/70 border-2 border-ink/40 flex items-center justify-center shrink-0" />
                )}

                {/* Step Text Label */}
                <span
                  className={`text-xs sm:text-[13px] leading-tight transition-colors ${
                    isActive
                      ? "text-[#006ee9] font-black"
                      : isCompleted
                        ? "text-ink font-bold"
                        : "text-ink/45 font-semibold"
                  }`}
                >
                  {stepLabel}
                </span>
              </div>
            );
          })}
        </div>

        {/* Progress Percentage and Step Counter */}
        <div className="mt-4 sm:mt-5 flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-black text-ink">{percentage}% Complete</span>
            <span className="font-bold text-ink/60">
              Step {displayStepNumber} of {ASSESSMENT_STEPS.length}
            </span>
          </div>

          {/* Horizontal Progress Bar */}
          <div
            className="h-3.5 sm:h-4 w-full bg-white border-2 border-ink rounded-full p-0.5 shadow-[1px_1px_0px_#000] overflow-hidden"
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className="h-full bg-lime border border-ink/30 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}

