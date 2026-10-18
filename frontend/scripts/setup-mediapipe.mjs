// Puts the MediaPipe Face Landmarker runtime and model under public/mediapipe so the mock
// interview's delivery analysis runs locally in the browser (no CDN, no video upload).
// Idempotent: existing files are kept. Runs before `npm run dev` / `npm run build`.
import { copyFileSync, existsSync, mkdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "node_modules/@mediapipe/tasks-vision/wasm");
const out = join(root, "public/mediapipe");
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

mkdirSync(join(out, "wasm"), { recursive: true });

for (const f of [
  "vision_wasm_internal.js",
  "vision_wasm_internal.wasm",
  "vision_wasm_nosimd_internal.js",
  "vision_wasm_nosimd_internal.wasm",
]) {
  const from = join(src, f);
  const to = join(out, "wasm", f);
  if (!existsSync(from)) {
    console.warn(`[mediapipe] ${f} missing; run npm install`);
    continue;
  }
  if (!existsSync(to) || statSync(to).size !== statSync(from).size) copyFileSync(from, to);
}

const model = join(out, "face_landmarker.task");
if (!existsSync(model)) {
  try {
    const res = await fetch(MODEL_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    writeFileSync(model, Buffer.from(await res.arrayBuffer()));
    console.log("[mediapipe] downloaded face_landmarker.task");
  } catch (err) {
    // The interview still works; only the camera-based delivery analysis is unavailable
    console.warn(`[mediapipe] couldn't download the face model (${err.message}); delivery analysis disabled`);
  }
}
