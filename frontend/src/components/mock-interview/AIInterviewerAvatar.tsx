"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Image from "next/image";
import type { LiveAvatarSession } from "@heygen/liveavatar-web-sdk";
import { Volume2, VolumeX, RotateCcw, Sparkles, ShieldCheck, Radio, Mic, Video, Loader2 } from "lucide-react";
import { ragApi, apiUrl } from "@/lib/ragApi";

// "live": photorealistic LiveAvatar video stream (lip-sync, blinking, head & hand gestures)
// "local": local avatar engine (LivePortrait head motion + blinks, MuseTalk lip-sync) rendering
//          each question to a clip, with an idle loop in between
// "fallback": still portraits + browser speech synthesis when no avatar is available
type AvatarMode = "connecting" | "live" | "local" | "fallback";

const CONNECT_TIMEOUT_MS = 20000;
const JOB_POLL_MS = 800;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

interface AIInterviewerAvatarProps {
  currentTextToSpeak?: string;
  /** Increment to make the interviewer speak `currentTextToSpeak` (new question, replay, etc.) */
  speakRequest?: number;
  /** Local-avatar render the backend already started for `currentTextToSpeak` */
  avatarJobId?: string | null;
  interviewState: "idle" | "speaking" | "listening" | "thinking";
  onSpeechEnd?: () => void;
  onSpeechStart?: () => void;
  topic?: string;
  difficulty?: string;
}

export default function AIInterviewerAvatar({
  currentTextToSpeak = "",
  speakRequest = 0,
  avatarJobId = null,
  interviewState = "idle",
  onSpeechEnd,
  onSpeechStart,
  topic = "General Technical",
  difficulty = "Entry Level",
}: AIInterviewerAvatarProps) {
  const [mode, setMode] = useState<AvatarMode>("connecting");
  const [fallbackReason, setFallbackReason] = useState("");
  const [isSandbox, setIsSandbox] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const sessionRef = useRef<LiveAvatarSession | null>(null);
  const modeRef = useRef<AvatarMode>("connecting");
  const pendingTextRef = useRef<string | null>(null);
  const isMutedRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const selectedVoiceRef = useRef<SpeechSynthesisVoice | null>(null);
  const callbacksRef = useRef({ onSpeechStart, onSpeechEnd });

  // Local avatar: idle loop URL, finished clips by text (instant replay), render jobs by text,
  // and a token that cancels an in-flight wait when the candidate interrupts or a new question arrives
  const [localStatus, setLocalStatus] = useState("");
  const [needsClickToPlay, setNeedsClickToPlay] = useState(false);
  const idleUrlRef = useRef<string | null>(null);
  const clipCacheRef = useRef(new Map<string, string>());
  const jobIdsRef = useRef(new Map<string, string>());
  const speakTokenRef = useRef(0);

  useEffect(() => {
    callbacksRef.current = { onSpeechStart, onSpeechEnd };
    isMutedRef.current = isMuted;
    selectedVoiceRef.current = selectedVoice;
  });

  const handleSpeechStart = useCallback(() => {
    isSpeakingRef.current = true;
    setIsSpeaking(true);
    callbacksRef.current.onSpeechStart?.();
  }, []);

  const handleSpeechEnd = useCallback(() => {
    isSpeakingRef.current = false;
    setIsSpeaking(false);
    callbacksRef.current.onSpeechEnd?.();
  }, []);

  // Browser speech synthesis (fallback voice)
  const speakWithBrowser = useCallback(
    (text: string) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      if (selectedVoiceRef.current) utterance.voice = selectedVoiceRef.current;
      utterance.rate = 1.0;
      utterance.pitch = 1.05;
      utterance.onstart = handleSpeechStart;
      utterance.onend = handleSpeechEnd;
      utterance.onerror = handleSpeechEnd;
      window.speechSynthesis.speak(utterance);
    },
    [handleSpeechStart, handleSpeechEnd]
  );

  // Local avatar: silent idle loop (head motion + blinks) whenever the interviewer isn't talking
  const showIdle = useCallback(() => {
    const video = videoRef.current;
    if (!video || !idleUrlRef.current) return;
    video.onended = null;
    video.onplaying = null;
    video.src = idleUrlRef.current;
    video.loop = true;
    video.muted = true;
    video.play().catch(() => {});
  }, []);

  const playClip = useCallback(
    (url: string) => {
      const video = videoRef.current;
      if (!video) return;
      setNeedsClickToPlay(false);
      video.onplaying = () => {
        video.onplaying = null;
        handleSpeechStart();
      };
      video.onended = () => {
        video.onended = null;
        handleSpeechEnd();
        showIdle();
      };
      video.src = url;
      video.loop = false;
      video.muted = isMutedRef.current;
      // Autoplay with sound can be blocked (e.g. Safari) when the render finished long after the click
      video.play().catch(() => setNeedsClickToPlay(true));
    },
    [handleSpeechStart, handleSpeechEnd, showIdle]
  );

  const speakLocal = useCallback(
    async (text: string) => {
      const token = ++speakTokenRef.current;
      const stillWanted = () => token === speakTokenRef.current;
      // A new question replaces whatever clip is still playing; go quiet until it's ready
      if (videoRef.current && !videoRef.current.loop) {
        if (isSpeakingRef.current) handleSpeechEnd();
        showIdle();
      }
      try {
        let url = clipCacheRef.current.get(text);
        if (!url) {
          setLocalStatus("Interviewer is preparing…");
          let jobId = jobIdsRef.current.get(text);
          if (!jobId) {
            jobId = (await ragApi.renderAvatarClip(text)).job_id;
            jobIdsRef.current.set(text, jobId);
          }
          while (!url) {
            if (!stillWanted()) return;
            const job = await ragApi.getAvatarJob(jobId);
            if (job.status === "done" && job.video_url) {
              url = apiUrl(job.video_url);
            } else if (job.status === "error") {
              throw new Error(job.error || "Avatar render failed");
            } else {
              setLocalStatus(
                job.status === "queued" && job.queued_ahead
                  ? `Interviewer is preparing… (${job.queued_ahead} ahead)`
                  : "Interviewer is preparing…"
              );
              await sleep(JOB_POLL_MS);
            }
          }
          clipCacheRef.current.set(text, url);
        }
        if (!stillWanted()) return;
        setLocalStatus("");
        playClip(url);
      } catch (err) {
        if (!stillWanted()) return;
        jobIdsRef.current.delete(text);
        setLocalStatus("");
        console.warn("Local avatar clip unavailable, using fallback voice:", err);
        speakWithBrowser(text);
      }
    },
    [playClip, speakWithBrowser, handleSpeechEnd, showIdle]
  );

  const speak = useCallback(
    (text: string) => {
      if (!text || isMutedRef.current) return;

      if (modeRef.current === "connecting") {
        // Spoken as soon as the human avatar stream is ready (or by the fallback voice)
        pendingTextRef.current = text;
        return;
      }

      if (modeRef.current === "local") {
        speakLocal(text);
        return;
      }

      const session = sessionRef.current;
      if (modeRef.current === "live" && session) {
        try {
          session.interrupt();
          session.repeat(text);
          return;
        } catch (err) {
          console.warn("LiveAvatar repeat failed, using fallback voice:", err);
        }
      }
      speakWithBrowser(text);
    },
    [speakWithBrowser, speakLocal]
  );

  // Silences the interviewer; the speech-ended event then resets the speaking state
  const haltAudio = useCallback(() => {
    if (modeRef.current === "local") {
      speakTokenRef.current++;            // abandon any clip still rendering
      setLocalStatus("");
      setNeedsClickToPlay(false);
      if (videoRef.current && !videoRef.current.loop) showIdle();
    }
    if (modeRef.current === "live" && sessionRef.current) {
      try {
        sessionRef.current.interrupt();
      } catch {
        /* session already closed */
      }
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  }, [showIdle]);

  const stopSpeaking = useCallback(() => {
    haltAudio();
    if (isSpeakingRef.current) handleSpeechEnd();
  }, [haltAudio, handleSpeechEnd]);

  const switchMode = useCallback(
    (next: AvatarMode, reason = "") => {
      if (modeRef.current === next) return;
      modeRef.current = next;
      setMode(next);
      setFallbackReason(reason);

      const pending = pendingTextRef.current;
      pendingTextRef.current = null;

      if (next === "fallback") {
        speakTokenRef.current++;
        setLocalStatus("");
        videoRef.current?.pause();
        const session = sessionRef.current;
        sessionRef.current = null;
        session?.stop().catch(() => {});
        if (isSpeakingRef.current) handleSpeechEnd();
      }
      if (pending) speak(pending);
    },
    [speak, handleSpeechEnd]
  );

  // Connect to the LiveAvatar streaming session once for the interview
  useEffect(() => {
    let cancelled = false;
    let session: LiveAvatarSession | null = null;
    // The video can be ready before start() resolves, but commands only work once connected
    let streamReady = false;
    let connected = false;
    const goLiveWhenReady = () => {
      if (!cancelled && streamReady && connected) switchMode("live");
    };

    // Deferred so React Strict Mode's mount/unmount/mount doesn't open (and pay for) two sessions
    const startTimer = setTimeout(async () => {
      // Which interviewer the backend is configured for; HeyGen is assumed if it can't say
      const config = await ragApi.getAvatarConfig().catch(() => null);
      if (cancelled) return;
      if (config?.provider === "local") {
        if (config.available && config.idle_video_url) {
          idleUrlRef.current = apiUrl(config.idle_video_url);
          showIdle();
          switchMode("local");
        } else {
          console.warn("Local avatar unavailable:", config.detail);
          switchMode("fallback", "Local avatar offline");
        }
        return;
      }
      if (config?.provider === "none") {
        switchMode("fallback", "Portrait mode");
        return;
      }

      try {
        const token = await ragApi.getAvatarSessionToken();
        const sdk = await import("@heygen/liveavatar-web-sdk");
        if (cancelled) return;
        setIsSandbox(token.is_sandbox);

        session = new sdk.LiveAvatarSession(token.session_token, {
          // The candidate's mic goes to our own Whisper pipeline, never to LiveAvatar
          voiceChat: { defaultMuted: true },
          autoKeepAlive: true,
        });
        sessionRef.current = session;

        session.on(sdk.SessionEvent.SESSION_STREAM_READY, () => {
          if (cancelled || !session) return;
          if (videoRef.current) session.attach(videoRef.current);
          streamReady = true;
          goLiveWhenReady();
        });
        session.on(sdk.AgentEventsEnum.AVATAR_SPEAK_STARTED, handleSpeechStart);
        session.on(sdk.AgentEventsEnum.AVATAR_SPEAK_ENDED, handleSpeechEnd);
        session.on(sdk.SessionEvent.SESSION_DISCONNECTED, () => {
          if (cancelled || sessionRef.current !== session) return;
          switchMode("fallback", "Avatar session ended");
        });

        await session.start();
        if (cancelled) {
          await session.stop();
          return;
        }
        connected = true;
        goLiveWhenReady();
      } catch (err) {
        console.warn("LiveAvatar unavailable, using portrait + browser voice:", err);
        if (!cancelled) switchMode("fallback", "Live avatar unavailable");
      }
    }, 0);

    const connectTimeout = setTimeout(() => {
      if (!cancelled && modeRef.current === "connecting") {
        switchMode("fallback", "Live avatar timed out");
      }
    }, CONNECT_TIMEOUT_MS);

    const speakToken = speakTokenRef;
    return () => {
      cancelled = true;
      speakToken.current++;               // abandon any clip still rendering
      clearTimeout(startTimer);
      clearTimeout(connectTimeout);
      sessionRef.current = null;
      session?.stop().catch(() => {});
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [switchMode, handleSpeechStart, handleSpeechEnd, showIdle]);

  // Initialize browser speech synthesis voices (fallback mode)
  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    const updateVoices = () => {
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
    };

    updateVoices();
    window.speechSynthesis.onvoiceschanged = updateVoices;
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  // Remember the render the backend started for this question (declared before the speak
  // effect below so the job id is known by the time that effect runs in the same render)
  useEffect(() => {
    if (avatarJobId && currentTextToSpeak) jobIdsRef.current.set(currentTextToSpeak, avatarJobId);
  }, [avatarJobId, currentTextToSpeak]);

  // Speak whenever the studio requests it (new question)
  useEffect(() => {
    if (speakRequest > 0) speak(currentTextToSpeak);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [speakRequest]);

  // Human gestures for the interview phases: attentive listening pose while the candidate answers
  useEffect(() => {
    // Local mode also cancels a clip that is still rendering, so it can't start over the answer
    if (interviewState === "listening" && (isSpeakingRef.current || modeRef.current === "local")) haltAudio();

    const session = sessionRef.current;
    if (mode !== "live" || !session) return;
    try {
      if (interviewState === "listening") session.startListening();
      else session.stopListening();
    } catch {
      /* session already closed */
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interviewState, mode]);

  // Mute only silences the live stream's audio; the avatar keeps its natural idle motion.
  // The local idle loop is always silent; only spoken clips follow the mute toggle.
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = mode === "local" && video.loop ? true : isMuted;
  }, [isMuted, mode]);

  const showsVideo = mode === "live" || mode === "local";

  // Determine avatar portrait based on current state (fallback mode)
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
        {/* Live avatar stream or local avatar clips; always mounted so the SDK can attach to it */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className={`absolute inset-0 h-full w-full ${mode === "local" ? "object-contain" : "object-cover"} ${
            showsVideo ? "opacity-100" : "opacity-0"
          }`}
        />

        {!showsVideo && (
          <Image
            src={getAvatarImageSrc()}
            alt="Elena Vance — AI Interviewer"
            fill
            priority
            sizes="(max-width: 768px) 100vw, 50vw"
            className="object-cover transition-opacity duration-300"
          />
        )}

        {/* Stream mode badge */}
        <div className="absolute left-3 top-3 flex items-center gap-1.5 border border-ink bg-white/95 px-2 py-0.5 text-[11px] font-bold text-ink shadow-[2px_2px_0_var(--color-ink)]">
          {mode === "connecting" && (
            <>
              <Loader2 className="size-3 animate-spin" /> Connecting live interviewer...
            </>
          )}
          {mode === "live" && (
            <>
              <Video className="size-3 text-brand-blue" /> Live Human Avatar{isSandbox ? " • Sandbox" : ""}
            </>
          )}
          {mode === "local" && (
            <>
              <Video className="size-3 text-brand-blue" /> Local Human Avatar
            </>
          )}
          {mode === "fallback" && <>{fallbackReason || "Portrait mode"} • Voice fallback</>}
        </div>

        {/* Local avatar: the spoken clip is still rendering */}
        {mode === "local" && localStatus && (
          <div className="absolute bottom-4 left-4 right-4 flex items-center justify-center gap-2 border-2 border-ink bg-white/95 px-4 py-2 shadow-[2px_2px_0_var(--color-ink)]">
            <Loader2 className="size-4 animate-spin text-ink" />
            <span className="text-xs font-bold text-ink">{localStatus}</span>
          </div>
        )}

        {/* Local avatar: the browser blocked autoplay with sound */}
        {mode === "local" && needsClickToPlay && (
          <button
            onClick={() => {
              setNeedsClickToPlay(false);
              videoRef.current?.play().catch(() => setNeedsClickToPlay(true));
            }}
            className="hard-shadow absolute z-10 flex items-center gap-2 bg-lime px-4 py-2 font-condensed text-sm font-bold uppercase tracking-wider text-ink"
          >
            <Volume2 className="size-4" /> Play interviewer
          </button>
        )}

        {/* Voice visualizer overlay for the portrait fallback (the video avatars lip-sync themselves) */}
        {!showsVideo && (interviewState === "speaking" || isSpeaking) && (
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
              Attentively listening to candidate&apos;s spoken response...
            </span>
          </div>
        )}
      </div>

      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t-2 border-ink bg-cream p-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => (isSpeaking ? stopSpeaking() : speak(currentTextToSpeak))}
            disabled={!currentTextToSpeak || mode === "connecting"}
            className="hard-shadow-sm flex items-center gap-1.5 bg-butter px-3 py-1.5 text-xs font-bold text-ink transition-transform hover:-translate-y-0.5 disabled:opacity-50"
            title="Repeat Question"
          >
            <RotateCcw className="size-3.5" /> Replay Voice
          </button>

          <button
            onClick={() => {
              const newMuted = !isMuted;
              setIsMuted(newMuted);
              if (newMuted && isSpeaking) stopSpeaking();
            }}
            className={`hard-shadow-sm flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold transition-transform hover:-translate-y-0.5 ${
              isMuted ? "bg-pink text-ink" : "bg-white text-ink"
            }`}
          >
            {isMuted ? <VolumeX className="size-3.5" /> : <Volume2 className="size-3.5" />}
            {isMuted ? "Muted" : "Voice On"}
          </button>
        </div>

        {/* Voice Selector (browser voices only apply to the portrait fallback) */}
        {mode === "fallback" && availableVoices.length > 0 && (
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

        {showsVideo && (
          <span className="text-[11px] font-bold text-muted">
            {topic} • {difficulty}
          </span>
        )}
      </div>
    </div>
  );
}
