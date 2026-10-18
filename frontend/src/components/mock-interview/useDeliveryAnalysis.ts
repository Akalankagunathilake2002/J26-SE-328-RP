"use client";

// Measures observable delivery cues from the candidate's camera while they answer, using the
// MediaPipe Face Landmarker (blendshapes + head pose). Everything runs in the browser: no video
// or images are sent anywhere. It reports what can be observed (eye contact, smiling, furrowed
// brows, blinking, head movement, face in view); it deliberately does not infer emotions or mood,
// which expressions can't reliably reveal (and which the EU AI Act prohibits in education).

import { useCallback, useEffect, useRef, useState } from "react";
import type { FaceLandmarker } from "@mediapipe/tasks-vision";

export interface DeliveryMetrics {
  seconds: number;
  face_visible_ratio: number;
  eye_contact_ratio: number | null;
  smile_ratio: number | null;
  brow_tension_ratio: number | null;
  blink_rate_per_min: number | null;
  head_steadiness: number | null;
}

export interface LiveCues {
  faceVisible: boolean;
  lookingAtCamera: boolean;
}

type Status = "off" | "loading" | "ready" | "unavailable";

const SAMPLE_MS = 120; // ~8 fps is plenty for these cues and keeps the CPU/GPU load low
const LOOK_YAW_DEG = 15;
const LOOK_PITCH_DEG = 12;

interface Frame {
  t: number;
  face: boolean;
  yaw: number;
  pitch: number;
  gazeAway: number;
  smile: number;
  brow: number;
  blink: number;
}

let landmarkerPromise: Promise<FaceLandmarker> | null = null;

function loadLandmarker(): Promise<FaceLandmarker> {
  // One shared instance per page; the model is ~4 MB and takes a moment to initialise
  landmarkerPromise ??= (async () => {
    const { FaceLandmarker, FilesetResolver } = await import("@mediapipe/tasks-vision");
    const fileset = await FilesetResolver.forVisionTasks("/mediapipe/wasm");
    const options = {
      baseOptions: { modelAssetPath: "/mediapipe/face_landmarker.task", delegate: "GPU" as const },
      runningMode: "VIDEO" as const,
      numFaces: 1,
      outputFaceBlendshapes: true,
      outputFacialTransformationMatrixes: true,
    };
    try {
      return await FaceLandmarker.createFromOptions(fileset, options);
    } catch {
      // Some browsers can't use the GPU delegate; the CPU one is slower but fine at 8 fps
      return await FaceLandmarker.createFromOptions(fileset, {
        ...options,
        baseOptions: { ...options.baseOptions, delegate: "CPU" as const },
      });
    }
  })();
  landmarkerPromise.catch(() => {
    landmarkerPromise = null;
  });
  return landmarkerPromise;
}

const toDeg = (r: number) => (r * 180) / Math.PI;
const median = (xs: number[]) => {
  const s = [...xs].sort((a, b) => a - b);
  return s.length ? s[Math.floor(s.length / 2)] : 0;
};
const std = (xs: number[]) => {
  if (xs.length < 2) return 0;
  const m = xs.reduce((a, b) => a + b, 0) / xs.length;
  return Math.sqrt(xs.reduce((a, b) => a + (b - m) ** 2, 0) / xs.length);
};

function readFrame(lm: FaceLandmarker, video: HTMLVideoElement, t: number): Frame {
  const res = lm.detectForVideo(video, t);
  const shapes = res.faceBlendshapes?.[0]?.categories;
  const matrix = res.facialTransformationMatrixes?.[0]?.data;
  if (!shapes || !matrix) return { t, face: false, yaw: 0, pitch: 0, gazeAway: 0, smile: 0, brow: 0, blink: 0 };
  const b = (name: string) => shapes.find((c) => c.categoryName === name)?.score ?? 0;
  const avg = (l: string, r: string) => (b(l) + b(r)) / 2;
  // Column-major 4x4 head pose; rotation terms give yaw (left/right) and pitch (up/down)
  const m = matrix;
  const yaw = toDeg(Math.atan2(m[8], m[10]));
  const pitch = toDeg(Math.atan2(-m[9], m[5]));
  // Eyes turned away even when the head faces the screen
  const gazeAway = Math.max(
    avg("eyeLookOutLeft", "eyeLookInRight"),
    avg("eyeLookInLeft", "eyeLookOutRight"),
    avg("eyeLookUpLeft", "eyeLookUpRight"),
    avg("eyeLookDownLeft", "eyeLookDownRight")
  );
  return {
    t,
    face: true,
    yaw,
    pitch,
    gazeAway,
    smile: avg("mouthSmileLeft", "mouthSmileRight"),
    brow: avg("browDownLeft", "browDownRight"),
    blink: avg("eyeBlinkLeft", "eyeBlinkRight"),
  };
}

function summarise(frames: Frame[]): DeliveryMetrics | null {
  if (frames.length < 5) return null;
  const seconds = (frames[frames.length - 1].t - frames[0].t) / 1000;
  const faces = frames.filter((f) => f.face);
  const face_visible_ratio = faces.length / frames.length;
  if (faces.length < 5) {
    return { seconds, face_visible_ratio, eye_contact_ratio: null, smile_ratio: null,
             brow_tension_ratio: null, blink_rate_per_min: null, head_steadiness: null };
  }
  // "Looking at the camera" is judged against the candidate's own usual head position, so a
  // camera that sits slightly off-centre doesn't count against them
  const baseYaw = median(faces.map((f) => f.yaw));
  const basePitch = median(faces.map((f) => f.pitch));
  const looking = faces.filter(
    (f) => Math.abs(f.yaw - baseYaw) < LOOK_YAW_DEG && Math.abs(f.pitch - basePitch) < LOOK_PITCH_DEG && f.gazeAway < 0.5
  ).length;
  let blinks = 0;
  for (let i = 1; i < faces.length; i++) if (faces[i].blink > 0.5 && faces[i - 1].blink <= 0.5) blinks++;
  const spread = Math.sqrt(std(faces.map((f) => f.yaw)) ** 2 + std(faces.map((f) => f.pitch)) ** 2);
  const round = (x: number) => Math.round(x * 100) / 100;
  // Looking-at-camera counts frames where the face is visible; it is scaled by visibility so an
  // answer given mostly off-screen can't score high eye contact
  return {
    seconds: round(seconds),
    face_visible_ratio: round(face_visible_ratio),
    eye_contact_ratio: round((looking / faces.length) * face_visible_ratio),
    smile_ratio: round(faces.filter((f) => f.smile > 0.45).length / faces.length),
    brow_tension_ratio: round(faces.filter((f) => f.brow > 0.35).length / faces.length),
    blink_rate_per_min: seconds > 5 ? Math.round((blinks / seconds) * 60) : null,
    head_steadiness: round(Math.max(0, Math.min(1, 1 - spread / 12))),
  };
}

export function useDeliveryAnalysis(video: HTMLVideoElement | null, enabled: boolean) {
  const [status, setStatus] = useState<Status>("off");
  const [live, setLive] = useState<LiveCues>({ faceVisible: false, lookingAtCamera: false });
  const framesRef = useRef<Frame[]>([]);
  const collectingRef = useRef(false);
  const lastLiveRef = useRef<LiveCues>(live);

  useEffect(() => {
    if (!enabled || !video) {
      const off = setTimeout(() => setStatus("off"), 0);
      return () => clearTimeout(off);
    }
    let stopped = false;
    let timer: ReturnType<typeof setInterval> | undefined;
    const begin = setTimeout(() => setStatus("loading"), 0);

    loadLandmarker()
      .then((lm) => {
        if (stopped) return;
        setStatus("ready");
        let lastT = 0;
        timer = setInterval(() => {
          if (video.readyState < 2 || video.videoWidth === 0) return;
          const t = Math.max(performance.now(), lastT + 1); // timestamps must increase
          lastT = t;
          let frame: Frame;
          try {
            frame = readFrame(lm, video, t);
          } catch {
            return;
          }
          if (collectingRef.current) framesRef.current.push(frame);
          const next: LiveCues = {
            faceVisible: frame.face,
            lookingAtCamera: frame.face && Math.abs(frame.yaw) < 20 && Math.abs(frame.pitch) < 18 && frame.gazeAway < 0.5,
          };
          if (next.faceVisible !== lastLiveRef.current.faceVisible ||
              next.lookingAtCamera !== lastLiveRef.current.lookingAtCamera) {
            lastLiveRef.current = next;
            setLive(next);
          }
        }, SAMPLE_MS);
      })
      .catch((err) => {
        console.warn("Delivery analysis unavailable:", err);
        if (!stopped) setStatus("unavailable");
      });

    return () => {
      stopped = true;
      clearTimeout(begin);
      if (timer) clearInterval(timer);
    };
  }, [video, enabled]);

  /** Start measuring a new answer */
  const startCollecting = useCallback(() => {
    framesRef.current = [];
    collectingRef.current = true;
  }, []);

  /** Stop measuring and return the answer's delivery metrics (null if too little data) */
  const stopCollecting = useCallback((): DeliveryMetrics | null => {
    collectingRef.current = false;
    const metrics = summarise(framesRef.current);
    framesRef.current = [];
    return metrics;
  }, []);

  return { status, live, startCollecting, stopCollecting };
}
