"use client";

import React, { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { Volume2, VolumeX, RotateCcw, Sparkles, ShieldCheck, Radio, Mic } from "lucide-react";

interface AIInterviewerAvatarProps {
  currentTextToSpeak?: string;
  interviewState: "idle" | "speaking" | "listening" | "thinking";
  onSpeechEnd?: () => void;
  onSpeechStart?: () => void;
  topic?: string;
  difficulty?: string;
}

export default function AIInterviewerAvatar({
  currentTextToSpeak = "",
  interviewState = "idle",
  onSpeechEnd,
  onSpeechStart,
  topic = "General Technical",
  difficulty = "Entry Level",
}: AIInterviewerAvatarProps) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [spokenWordIndex, setSpokenWordIndex] = useState(-1);
  const [wordsList, setWordsList] = useState<string[]>([]);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Initialize browser speech synthesis voices
  useEffect(() => {
    const updateVoices = () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        const voices = window.speechSynthesis.getVoices();
        setAvailableVoices(voices);

        const preferred =
          voices.find(
            (v) =>
              v.lang.startsWith("en") &&
              (v.name.includes("Samantha") ||
                v.name.includes("Google US English") ||
                v.name.includes("Victoria") ||
                v.name.includes("Zira") ||
                v.name.includes("Karen") ||
                v.name.includes("Female"))
          ) ||
          voices.find((v) => v.lang.startsWith("en")) ||
          voices[0];

        if (preferred) setSelectedVoice(preferred);
      }
    };

    updateVoices();
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.onvoiceschanged = updateVoices;
    }

    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Split question into words for live transcript pacing
  useEffect(() => {
    if (currentTextToSpeak) {
      const words = currentTextToSpeak.split(/\s+/).filter(Boolean);
      setWordsList(words);
      setSpokenWordIndex(-1);
    }
  }, [currentTextToSpeak]);

  // Handle speaking question aloud
  const speakCurrentText = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    if (!currentTextToSpeak || isMuted) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(currentTextToSpeak);
    if (selectedVoice) utterance.voice = selectedVoice;
    utterance.rate = 1.0;
    utterance.pitch = 1.05;

    utterance.onstart = () => {
      setIsSpeaking(true);
      if (onSpeechStart) onSpeechStart();
    };

    utterance.onboundary = (event) => {
      if (event.name === "word") {
        const charIdx = event.charIndex;
        let cumulative = 0;
        for (let i = 0; i < wordsList.length; i++) {
          cumulative += wordsList[i].length + 1;
          if (cumulative > charIdx) {
            setSpokenWordIndex(i);
            break;
          }
        }
      }
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setSpokenWordIndex(-1);
      if (onSpeechEnd) onSpeechEnd();
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
      setSpokenWordIndex(-1);
      if (onSpeechEnd) onSpeechEnd();
    };

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  // Trigger speech when interview state switches to speaking
  useEffect(() => {
    if (interviewState === "speaking" && currentTextToSpeak && !isSpeaking) {
      speakCurrentText();
    } else if (interviewState !== "speaking" && isSpeaking) {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      setIsSpeaking(false);
    }
  }, [interviewState, currentTextToSpeak]);

  // Determine avatar portrait based on current state
  const getAvatarImageSrc = () => {
    if (interviewState === "listening") {
      return "/interviewer/avatar_listening.jpg";
    }
    if (interviewState === "speaking" || isSpeaking) {
      return "/interviewer/avatar_speaking.jpg";
    }
    return "/interviewer/avatar_neutral.jpg";
  };

  return (
    <div className="border-2 border-ink bg-white shadow-[5px_5px_0_var(--color-ink)] flex flex-col overflow-hidden">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b-2 border-ink bg-cream px-4 py-2.5">
        <div className="flex items-center gap-2">
          <ShieldCheck className="size-4 text-brand-blue" />
          <span className="font-condensed text-base font-bold uppercase tracking-wider text-ink">
            Elena Vance • AI Lead Interviewer
          </span>
        </div>
        <div className="flex items-center gap-2">
          {interviewState === "speaking" && (
            <span className="flex items-center gap-1.5 border border-ink bg-lime px-2 py-0.5 text-[11px] font-bold text-ink animate-pulse">
              <Radio className="size-3 text-ink" /> Speaking
            </span>
          )}
          {interviewState === "listening" && (
            <span className="flex items-center gap-1.5 border border-ink bg-cyan px-2 py-0.5 text-[11px] font-bold text-ink animate-pulse">
              <Mic className="size-3 text-ink" /> Listening
            </span>
          )}
          {interviewState === "thinking" && (
            <span className="flex items-center gap-1.5 border border-ink bg-pink px-2 py-0.5 text-[11px] font-bold text-ink">
              <Sparkles className="size-3 text-ink" /> Analyzing
            </span>
          )}
          {interviewState === "idle" && (
            <span className="border border-ink bg-sand px-2 py-0.5 text-[11px] font-bold text-muted">
              Standby
            </span>
          )}
        </div>
      </div>

      {/* Main Avatar Stage */}
      <div className="relative aspect-video w-full bg-slate-900 overflow-hidden flex items-center justify-center">
        <Image
          src={getAvatarImageSrc()}
          alt="Elena Vance — AI Interviewer"
          fill
          priority
          sizes="(max-width: 768px) 100vw, 50vw"
          className="object-cover transition-opacity duration-300"
        />

        {/* Live Audio Visualizer Overlay when speaking */}
        {(interviewState === "speaking" || isSpeaking) && (
          <div className="absolute bottom-4 left-4 right-4 flex items-center justify-center gap-1.5 rounded-lg border-2 border-ink bg-white/95 px-3 py-2 shadow-[2px_2px_0_var(--color-ink)] backdrop-blur-sm">
            <span className="mr-2 text-xs font-bold text-ink">Elena Voice Audio:</span>
            {[0.6, 1.0, 0.4, 0.8, 1.2, 0.5, 0.9, 0.7].map((height, idx) => (
              <span
                key={idx}
                className="w-1.5 bg-brand-blue rounded-full animate-bounce"
                style={{
                  height: `${height * 16}px`,
                  animationDelay: `${idx * 100}ms`,
                  animationDuration: "600ms",
                }}
              />
            ))}
          </div>
        )}

        {/* Active Listening Indicator */}
        {interviewState === "listening" && (
          <div className="absolute bottom-4 left-4 right-4 flex items-center justify-center gap-2 border-2 border-ink bg-cyan/95 px-4 py-2 shadow-[2px_2px_0_var(--color-ink)]">
            <Mic className="size-4 text-ink animate-pulse" />
            <span className="text-xs font-bold text-ink">
              Attentively listening to candidate's spoken response...
            </span>
          </div>
        )}
      </div>

      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t-2 border-ink bg-cream p-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (isSpeaking) {
                window.speechSynthesis.cancel();
                setIsSpeaking(false);
              } else {
                speakCurrentText();
              }
            }}
            disabled={!currentTextToSpeak}
            className="hard-shadow-sm flex items-center gap-1.5 bg-butter px-3 py-1.5 text-xs font-bold text-ink transition-transform hover:-translate-y-0.5 disabled:opacity-50"
            title="Repeat Question"
          >
            <RotateCcw className="size-3.5" /> Replay Voice
          </button>

          <button
            onClick={() => {
              const newMuted = !isMuted;
              setIsMuted(newMuted);
              if (newMuted && isSpeaking) {
                window.speechSynthesis.cancel();
                setIsSpeaking(false);
              }
            }}
            className={`hard-shadow-sm flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold transition-transform hover:-translate-y-0.5 ${
              isMuted ? "bg-pink text-ink" : "bg-white text-ink"
            }`}
          >
            {isMuted ? <VolumeX className="size-3.5" /> : <Volume2 className="size-3.5" />}
            {isMuted ? "Muted" : "Voice On"}
          </button>
        </div>

        {/* Voice Selector */}
        {availableVoices.length > 0 && (
          <div className="flex items-center gap-1 text-xs">
            <span className="font-bold text-muted hidden sm:inline">Voice:</span>
            <select
              value={selectedVoice?.name || ""}
              onChange={(e) => {
                const found = availableVoices.find((v) => v.name === e.target.value);
                if (found) setSelectedVoice(found);
              }}
              className="border border-ink bg-white px-2 py-1 text-xs font-medium text-ink shadow-[2px_2px_0_var(--color-ink)] focus:outline-none"
            >
              {availableVoices
                .filter((v) => v.lang.startsWith("en"))
                .slice(0, 6)
                .map((v) => (
                  <option key={v.name} value={v.name}>
                    {v.name.slice(0, 22)}
                  </option>
                ))}
            </select>
          </div>
        )}
      </div>
    </div>
  );
}
