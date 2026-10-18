"use client";

import React, { useState, useEffect, useRef } from "react";
import { CameraOff, Mic, MicOff, Video, AlertCircle, Eye, EyeOff, ScanFace } from "lucide-react";
import type { LiveCues } from "./useDeliveryAnalysis";

interface CandidateWebcamProps {
  candidateName?: string;
  candidateId?: string;
  isRecordingAnswer?: boolean;
  /** Camera on/off is controlled by the interview control bar */
  videoOn: boolean;
  micOn: boolean;
  /** Receives the <video> element so delivery analysis can read frames from it */
  onVideoElement?: (el: HTMLVideoElement | null) => void;
  onCameraError?: (message: string) => void;
  analysisStatus?: "off" | "loading" | "ready" | "unavailable";
  liveCues?: LiveCues;
}

export default function CandidateWebcam({
  candidateName = "Candidate",
  candidateId = "",
  isRecordingAnswer = false,
  videoOn,
  micOn,
  onVideoElement,
  onCameraError,
  analysisStatus = "off",
  liveCues,
}: CandidateWebcamProps) {
  const [cameraActive, setCameraActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const callbacksRef = useRef({ onVideoElement, onCameraError });

  useEffect(() => {
    callbacksRef.current = { onVideoElement, onCameraError };
  });

  // Start/stop the camera when the control bar toggles it
  useEffect(() => {
    let cancelled = false;

    const stop = () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      audioContextRef.current?.close().catch(() => {});
      audioContextRef.current = null;
      setCameraActive(false);
      setAudioLevel(0);
      callbacksRef.current.onVideoElement?.(null);
    };

    if (!videoOn) {
      const t = setTimeout(stop, 0);
      return () => clearTimeout(t);
    }

    // Deferred so React Strict Mode's mount/unmount/mount doesn't open the camera twice
    const timer = setTimeout(async () => {
      try {
        setErrorMessage(null);
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: true });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        // The <video> element is always mounted, so the stream attaches right away
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        }
        setCameraActive(true);
        callbacksRef.current.onVideoElement?.(videoRef.current);

        // Mic level meter (the recording itself is handled by the interview studio)
        try {
          const AudioContextClass =
            window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
          const audioCtx = new AudioContextClass();
          audioContextRef.current = audioCtx;
          const analyser = audioCtx.createAnalyser();
          analyser.fftSize = 64;
          audioCtx.createMediaStreamSource(stream).connect(analyser);
          const data = new Uint8Array(analyser.frequencyBinCount);
          const tick = () => {
            analyser.getByteFrequencyData(data);
            const avg = data.reduce((a, b) => a + b, 0) / data.length;
            setAudioLevel(Math.min(100, Math.round(avg * 1.5)));
            animationFrameRef.current = requestAnimationFrame(tick);
          };
          tick();
        } catch (audioErr) {
          console.warn("Audio meter initialization skipped:", audioErr);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Camera permission denied or device not found.";
        console.warn("Camera access denied or device not found:", err);
        setErrorMessage(message);
        setCameraActive(false);
        callbacksRef.current.onCameraError?.(message);
      }
    }, 0);

    return () => {
      cancelled = true;
      clearTimeout(timer);
      stop();
    };
  }, [videoOn]);

  // The meter's mic track follows the mic toggle too
  useEffect(() => {
    streamRef.current?.getAudioTracks().forEach((t) => (t.enabled = micOn));
  }, [micOn, cameraActive]);

  return (
    <div className="border-2 border-ink bg-white shadow-[5px_5px_0_var(--color-ink)] flex flex-col overflow-hidden">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b-2 border-ink bg-cream px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Video className="size-4 text-brand-blue" />
          <span className="font-condensed text-base font-bold uppercase tracking-wider text-ink">{candidateName}</span>
        </div>
        <div className="flex items-center gap-2">
          {!micOn && (
            <span className="flex items-center gap-1 border border-ink bg-pink px-2 py-0.5 text-[11px] font-bold text-ink">
              <MicOff className="size-3" /> Muted
            </span>
          )}
          {cameraActive ? (
            <span className="flex items-center gap-1.5 border border-ink bg-lime px-2 py-0.5 text-[11px] font-bold text-ink">
              <span className="size-2 rounded-full bg-emerald-600 animate-ping" />
              Live Camera
            </span>
          ) : (
            <span className="border border-ink bg-sand px-2 py-0.5 text-[11px] font-bold text-muted">Camera Off</span>
          )}
        </div>
      </div>

      {/* Video stream viewport */}
      <div className="relative aspect-video w-full bg-slate-900 overflow-hidden flex items-center justify-center">
        {/* Always mounted: the stream is attached before React re-renders with cameraActive=true */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`absolute inset-0 w-full h-full object-cover -scale-x-100 ${cameraActive ? "" : "hidden"}`}
        />
        {!cameraActive && (
          <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
            <div className="grid size-16 place-items-center rounded-full border-2 border-ink bg-sand shadow-[2px_2px_0_var(--color-ink)]">
              <CameraOff className="size-8 text-muted" />
            </div>
            <p className="text-sm font-bold text-white">{videoOn ? "Starting camera…" : "Camera is off"}</p>
            <p className="text-xs text-slate-400 max-w-[260px]">
              {videoOn ? "Allow camera access when your browser asks." : "Turn it on with the camera button below."}
            </p>
            {errorMessage && (
              <p className="text-[11px] text-pink font-semibold flex items-center gap-1">
                <AlertCircle className="size-3" /> {errorMessage}
              </p>
            )}
          </div>
        )}

        {/* Live delivery cues (only when the candidate opted in) */}
        {cameraActive && analysisStatus !== "off" && (
          <div className="absolute left-3 top-3 flex flex-col gap-1.5">
            {analysisStatus === "loading" && (
              <span className="flex items-center gap-1 border border-ink bg-white/95 px-2 py-0.5 text-[11px] font-bold text-ink">
                <ScanFace className="size-3" /> Starting delivery analysis…
              </span>
            )}
            {analysisStatus === "unavailable" && (
              <span className="border border-ink bg-white/95 px-2 py-0.5 text-[11px] font-bold text-muted">
                Delivery analysis unavailable in this browser
              </span>
            )}
            {analysisStatus === "ready" && liveCues && (
              <span
                className={`flex items-center gap-1 border border-ink px-2 py-0.5 text-[11px] font-bold text-ink ${
                  !liveCues.faceVisible ? "bg-pink" : liveCues.lookingAtCamera ? "bg-lime" : "bg-butter"
                }`}
              >
                {liveCues.lookingAtCamera ? <Eye className="size-3" /> : <EyeOff className="size-3" />}
                {!liveCues.faceVisible ? "Face not in view" : liveCues.lookingAtCamera ? "Looking at camera" : "Looking away"}
              </span>
            )}
          </div>
        )}

        {/* Mic level + recording state */}
        {cameraActive && (
          <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between border-2 border-ink bg-white/95 px-3 py-1.5 shadow-[2px_2px_0_var(--color-ink)] backdrop-blur-sm text-xs">
            <div className="flex items-center gap-2">
              {micOn ? <Mic className="size-3.5 text-brand-blue" /> : <MicOff className="size-3.5 text-ink" />}
              <span className="font-bold text-ink">Mic:</span>
              <div className="w-24 h-2.5 border border-ink bg-sand rounded-sm overflow-hidden">
                <div className="h-full bg-lime transition-all duration-75" style={{ width: `${micOn ? audioLevel : 0}%` }} />
              </div>
            </div>
            {isRecordingAnswer && (
              <span className="border border-ink bg-pink px-2 py-0.5 text-[10px] font-bold text-ink animate-pulse">
                {micOn ? "Recording answer…" : "Paused (muted)"}
              </span>
            )}
          </div>
        )}
      </div>

      {candidateId && (
        <div className="flex items-center justify-end border-t-2 border-ink bg-cream px-3 py-2">
          <span className="text-xs font-mono font-semibold text-muted">Candidate ID: {candidateId}</span>
        </div>
      )}
    </div>
  );
}
