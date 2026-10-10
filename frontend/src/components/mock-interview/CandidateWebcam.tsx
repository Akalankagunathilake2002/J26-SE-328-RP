"use client";

import React, { useState, useEffect, useRef } from "react";
import { Camera, CameraOff, Mic, MicOff, Video, AlertCircle } from "lucide-react";

interface CandidateWebcamProps {
  candidateName?: string;
  candidateId?: string;
  targetRole?: string;
  isRecordingAnswer?: boolean;
}

export default function CandidateWebcam({
  candidateName = "Dilmith (Candidate)",
  candidateId = "stu_1024",
  targetRole = "Backend Developer",
  isRecordingAnswer = false,
}: CandidateWebcamProps) {
  const [cameraActive, setCameraActive] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Start candidate camera
  const startCamera = async () => {
    try {
      setErrorMessage(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: true,
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
      setHasPermission(true);

      // Setup audio analyzer for voice activity meter
      try {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        const audioCtx = new AudioContextClass();
        audioContextRef.current = audioCtx;
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        source.connect(analyser);
        analyserRef.current = analyser;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const updateAudioMeter = () => {
          analyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
          }
          const avg = sum / dataArray.length;
          setAudioLevel(Math.min(100, Math.round(avg * 1.5)));
          animationFrameRef.current = requestAnimationFrame(updateAudioMeter);
        };
        updateAudioMeter();
      } catch (audioErr) {
        console.warn("Audio meter initialization skipped:", audioErr);
      }
    } catch (err: any) {
      console.warn("Camera access denied or device not found:", err);
      setHasPermission(false);
      setErrorMessage(err.message || "Camera permission denied or device not found.");
      setCameraActive(false);
    }
  };

  // Stop candidate camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setCameraActive(false);
    setAudioLevel(0);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="border-2 border-ink bg-white shadow-[5px_5px_0_var(--color-ink)] flex flex-col overflow-hidden">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b-2 border-ink bg-cream px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Video className="size-4 text-brand-blue" />
          <span className="font-condensed text-base font-bold uppercase tracking-wider text-ink">
            {candidateName}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {cameraActive ? (
            <span className="flex items-center gap-1.5 border border-ink bg-lime px-2 py-0.5 text-[11px] font-bold text-ink">
              <span className="size-2 rounded-full bg-emerald-600 animate-ping" />
              Live Camera
            </span>
          ) : (
            <span className="border border-ink bg-sand px-2 py-0.5 text-[11px] font-bold text-muted">
              Camera Off
            </span>
          )}
        </div>
      </div>

      {/* Video stream viewport */}
      <div className="relative aspect-video w-full bg-slate-900 overflow-hidden flex items-center justify-center">
        {cameraActive ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover -scale-x-100"
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
            <div className="grid size-16 place-items-center rounded-full border-2 border-ink bg-sand shadow-[2px_2px_0_var(--color-ink)]">
              <CameraOff className="size-8 text-muted" />
            </div>
            <div>
              <p className="text-sm font-bold text-white">Candidate Camera Offline</p>
              <p className="text-xs text-slate-400 mt-1 max-w-[260px]">
                Turn on your camera for the realistic face-to-face AI mock interview boardroom experience.
              </p>
            </div>
            <button
              onClick={startCamera}
              className="hard-shadow-sm flex items-center gap-2 bg-lime px-4 py-2 text-xs font-bold text-ink transition-transform hover:-translate-y-0.5"
            >
              <Camera className="size-4 text-ink" /> Enable Camera & Mic
            </button>
            {errorMessage && (
              <p className="text-[11px] text-pink font-semibold flex items-center gap-1">
                <AlertCircle className="size-3" /> {errorMessage}
              </p>
            )}
          </div>
        )}

        {/* Live Audio Activity Level Indicator */}
        {cameraActive && (
          <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between border-2 border-ink bg-white/95 px-3 py-1.5 shadow-[2px_2px_0_var(--color-ink)] backdrop-blur-sm text-xs">
            <div className="flex items-center gap-2">
              <Mic className="size-3.5 text-brand-blue" />
              <span className="font-bold text-ink">Mic Input:</span>
              <div className="w-24 h-2.5 border border-ink bg-sand rounded-sm overflow-hidden">
                <div
                  className="h-full bg-lime transition-all duration-75"
                  style={{ width: `${audioLevel}%` }}
                />
              </div>
            </div>
            {isRecordingAnswer && (
              <span className="border border-ink bg-pink px-2 py-0.5 text-[10px] font-bold text-ink animate-pulse">
                Recording Answer...
              </span>
            )}
          </div>
        )}
      </div>

      {/* Controls bar */}
      <div className="flex items-center justify-between border-t-2 border-ink bg-cream p-3">
        <div className="flex items-center gap-2">
          {cameraActive ? (
            <button
              onClick={stopCamera}
              className="hard-shadow-sm flex items-center gap-1.5 bg-pink px-3 py-1.5 text-xs font-bold text-ink transition-transform hover:-translate-y-0.5"
            >
              <CameraOff className="size-3.5" /> Turn Off Camera
            </button>
          ) : (
            <button
              onClick={startCamera}
              className="hard-shadow-sm flex items-center gap-1.5 bg-lime px-3 py-1.5 text-xs font-bold text-ink transition-transform hover:-translate-y-0.5"
            >
              <Camera className="size-3.5" /> Turn On Camera
            </button>
          )}
        </div>
        <span className="text-xs font-mono font-semibold text-muted">
          Candidate ID: {candidateId}
        </span>
      </div>
    </div>
  );
}
