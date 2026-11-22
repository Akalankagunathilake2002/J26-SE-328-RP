/**
 * Records the whole mock interview in the browser as one video: Elena on the left, the candidate on the
 * right, both voices mixed, and what Elena says drawn as captions (the browser's built-in voice, used when
 * the avatar is off, can't be captured, so the captions keep the recording complete).
 *
 * The recording stays in memory in this tab until it is uploaded to the candidate's Drive or downloaded.
 */

const WIDTH = 1280;
const HEIGHT = 520;
const PANEL_H = 440; // video area; the rest is the caption bar
const FPS = 24;

export interface RecorderSources {
  /** The interviewer's <video> elements (the visible one is recorded) */
  interviewer: () => (HTMLVideoElement | null)[];
  /** The candidate's camera preview */
  candidate: () => HTMLVideoElement | null;
  /** What Elena is saying now, for the captions */
  caption: () => string;
  candidateName: string;
  title: string;
}

export interface Recording {
  blob: Blob;
  mimeType: string;
  extension: "mp4" | "webm";
  seconds: number;
}

const MIME_TYPES = [
  "video/mp4;codecs=avc1,mp4a.40.2",
  "video/mp4",
  "video/webm;codecs=vp9,opus",
  "video/webm;codecs=vp8,opus",
  "video/webm",
];

export const recordingSupported = () =>
  typeof window !== "undefined" &&
  typeof MediaRecorder !== "undefined" &&
  typeof HTMLCanvasElement.prototype.captureStream === "function" &&
  MIME_TYPES.some((t) => MediaRecorder.isTypeSupported(t));

// A media element can be connected to Web Audio only once in its lifetime, and from then on its sound
// plays only through that AudioContext, so one context is shared and never closed.
let sharedCtx: AudioContext | null = null;
const connected = new WeakMap<HTMLMediaElement, AudioNode>();

const sameOrigin = (v: HTMLVideoElement) => {
  if (v.srcObject) return true;
  const src = v.currentSrc || v.src;
  if (!src) return false;
  try {
    return new URL(src, location.href).origin === location.origin;
  } catch {
    return false;
  }
};

function drawCover(ctx: CanvasRenderingContext2D, v: HTMLVideoElement, x: number, y: number, w: number, h: number, contain: boolean) {
  const vw = v.videoWidth;
  const vh = v.videoHeight;
  if (!vw || !vh) return false;
  const scale = contain ? Math.min(w / vw, h / vh) : Math.max(w / vw, h / vh);
  const dw = vw * scale;
  const dh = vh * scale;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();
  ctx.drawImage(v, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
  ctx.restore();
  return true;
}

function wrap(ctx: CanvasRenderingContext2D, text: string, maxWidth: number, maxLines: number): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let line = "";
  for (const w of words) {
    const next = line ? `${line} ${w}` : w;
    if (ctx.measureText(next).width > maxWidth && line) {
      lines.push(line);
      line = w;
    } else line = next;
  }
  if (line) lines.push(line);
  // Keep the end of long speech (the latest words) rather than the start
  return lines.length > maxLines ? ["…" + lines[lines.length - maxLines].replace(/^\S+/, ""), ...lines.slice(-maxLines + 1)] : lines;
}

export class InterviewRecorder {
  private canvas = document.createElement("canvas");
  private recorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private timer: ReturnType<typeof setInterval> | null = null;
  private mic: MediaStream | null = null;
  private micGain: GainNode | null = null;
  private dest: MediaStreamAudioDestinationNode | null = null;
  private startedAt = 0;
  private mimeType = "";

  constructor(private sources: RecorderSources) {
    this.canvas.width = WIDTH;
    this.canvas.height = HEIGHT;
  }

  get active() {
    return this.recorder?.state === "recording";
  }

  async start() {
    const ctx2d = this.canvas.getContext("2d")!;
    sharedCtx ??= new AudioContext();
    await sharedCtx.resume().catch(() => {});
    this.dest = sharedCtx.createMediaStreamDestination();

    // The candidate's voice (its own capture, so muting in the control bar can be mirrored here)
    try {
      this.mic = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      this.micGain = sharedCtx.createGain();
      sharedCtx.createMediaStreamSource(this.mic).connect(this.micGain).connect(this.dest);
    } catch {
      this.mic = null; // recorded without the candidate's voice; the caller shows why
    }

    this.draw(ctx2d);
    this.timer = setInterval(() => this.draw(ctx2d), 1000 / FPS);

    const stream = new MediaStream([...this.canvas.captureStream(FPS).getVideoTracks(), ...this.dest.stream.getAudioTracks()]);
    this.mimeType = MIME_TYPES.find((t) => MediaRecorder.isTypeSupported(t)) ?? "";
    this.recorder = new MediaRecorder(stream, {
      mimeType: this.mimeType,
      videoBitsPerSecond: 900_000, // about 7 MB a minute
      audioBitsPerSecond: 96_000,
    });
    this.chunks = [];
    this.recorder.ondataavailable = (e) => e.data.size && this.chunks.push(e.data);
    this.recorder.start(5000);
    this.startedAt = Date.now();
    return { micCaptured: !!this.mic };
  }

  setMicEnabled(on: boolean) {
    if (this.micGain) this.micGain.gain.value = on ? 1 : 0;
  }

  /** Routes an interviewer video's sound into the recording as well as the speakers */
  private captureAudio(v: HTMLVideoElement) {
    if (!sharedCtx || !this.dest || sharedCtx.state !== "running") return;
    let node = connected.get(v);
    if (!node) {
      if (v.srcObject instanceof MediaStream) {
        if (!v.srcObject.getAudioTracks().length) return;
        node = sharedCtx.createMediaStreamSource(v.srcObject); // a live stream still plays through the element
      } else {
        if (!sameOrigin(v)) return; // cross-origin audio would come out silent, for the candidate too
        node = sharedCtx.createMediaElementSource(v);
        node.connect(sharedCtx.destination); // keep it audible
      }
      connected.set(v, node);
    }
    try {
      node.connect(this.dest);
    } catch {
      /* already connected */
    }
  }

  private draw(ctx: CanvasRenderingContext2D) {
    const half = WIDTH / 2;
    ctx.fillStyle = "#111827";
    ctx.fillRect(0, 0, WIDTH, HEIGHT);

    // Elena: the player that is showing (the local avatar swaps between two)
    const players = this.sources.interviewer().filter((v): v is HTMLVideoElement => !!v);
    for (const v of players) this.captureAudio(v);
    const visible =
      players.find((v) => !v.paused && v.style.opacity !== "0" && v.readyState >= 2) ??
      players.find((v) => v.readyState >= 2 && v.style.opacity !== "0");
    const drewElena = visible && sameOrigin(visible) && drawCover(ctx, visible, 0, 0, half, PANEL_H, true);
    if (!drewElena) {
      ctx.fillStyle = "#1f2937";
      ctx.fillRect(0, 0, half, PANEL_H);
      ctx.fillStyle = "#e5e7eb";
      ctx.font = "bold 28px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Elena (AI interviewer)", half / 2, PANEL_H / 2);
    }

    const cam = this.sources.candidate();
    if (!(cam && drawCover(ctx, cam, half, 0, half, PANEL_H, false))) {
      ctx.fillStyle = "#374151";
      ctx.fillRect(half, 0, half, PANEL_H);
      ctx.fillStyle = "#e5e7eb";
      ctx.font = "bold 24px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Camera off", half + half / 2, PANEL_H / 2);
    }

    // Name labels
    ctx.font = "bold 16px system-ui, sans-serif";
    ctx.textAlign = "left";
    for (const [label, x] of [["Elena · AI interviewer", 12], [this.sources.candidateName, half + 12]] as const) {
      const w = ctx.measureText(label).width + 16;
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(x, PANEL_H - 36, w, 26);
      ctx.fillStyle = "#fff";
      ctx.fillText(label, x + 8, PANEL_H - 18);
    }

    // Caption bar: Elena's words, title and running time
    ctx.fillStyle = "#000";
    ctx.fillRect(0, PANEL_H, WIDTH, HEIGHT - PANEL_H);
    ctx.font = "18px system-ui, sans-serif";
    ctx.fillStyle = "#fde68a";
    const lines = wrap(ctx, this.sources.caption(), WIDTH - 220, 3);
    lines.forEach((l, i) => ctx.fillText(l, 12, PANEL_H + 24 + i * 22));
    const secs = this.startedAt ? Math.floor((Date.now() - this.startedAt) / 1000) : 0;
    ctx.textAlign = "right";
    ctx.fillStyle = "#9ca3af";
    ctx.font = "14px system-ui, sans-serif";
    ctx.fillText(`${this.sources.title} · ${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`, WIDTH - 12, HEIGHT - 10);
    ctx.textAlign = "left";
  }

  /** Stops and returns the finished recording */
  stop(): Promise<Recording | null> {
    const rec = this.recorder;
    const cleanup = () => {
      if (this.timer) clearInterval(this.timer);
      this.timer = null;
      this.mic?.getTracks().forEach((t) => t.stop());
      this.mic = null;
      this.dest?.disconnect();
      this.recorder = null;
    };
    if (!rec || rec.state === "inactive") {
      cleanup();
      return Promise.resolve(null);
    }
    const seconds = Math.round((Date.now() - this.startedAt) / 1000);
    return new Promise((resolve) => {
      rec.onstop = () => {
        cleanup();
        const type = this.mimeType.split(";")[0] || "video/webm";
        const blob = new Blob(this.chunks, { type });
        this.chunks = [];
        resolve(blob.size ? { blob, mimeType: type, extension: type.includes("mp4") ? "mp4" : "webm", seconds } : null);
      };
      rec.stop();
    });
  }

  /** Throws the recording away (leaving the page mid-interview) */
  discard() {
    this.chunks = [];
    if (this.recorder && this.recorder.state !== "inactive") {
      this.recorder.ondataavailable = null;
      this.recorder.onstop = null;
      this.recorder.stop();
    }
    if (this.timer) clearInterval(this.timer);
    this.mic?.getTracks().forEach((t) => t.stop());
  }
}
