/**
 * Saves interview recordings to the candidate's own Google Drive, straight from the browser.
 *
 * Google Identity Services gives a short-lived access token (about an hour) for the `drive.file` scope only:
 * the app can create files and see the files it created, nothing else in the candidate's Drive. The
 * recording goes browser -> Google; Skillaro's servers never receive it. Needs NEXT_PUBLIC_GOOGLE_CLIENT_ID
 * (an OAuth "Web application" client whose authorised JavaScript origins include this site).
 */

const SCOPE = "https://www.googleapis.com/auth/drive.file";
const FOLDER_NAME = "Skillaro Interviews";
const CHUNK = 8 * 1024 * 1024; // resumable upload chunk: a multiple of 256 KiB

interface TokenResponse {
  access_token?: string;
  expires_in?: number;
  error?: string;
  error_description?: string;
}
interface TokenClient {
  requestAccessToken: (overrides?: { prompt?: string }) => void;
}
declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initTokenClient: (config: {
            client_id: string;
            scope: string;
            callback: (resp: TokenResponse) => void;
            error_callback?: (err: { type: string; message?: string }) => void;
          }) => TokenClient;
        };
      };
    };
  }
}

export const driveClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";
export const driveAvailable = () => !!driveClientId;

let token: { value: string; expiresAt: number } | null = null;
let scriptPromise: Promise<void> | null = null;

function loadScript(): Promise<void> {
  if (window.google?.accounts?.oauth2) return Promise.resolve();
  scriptPromise ??= new Promise<void>((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "https://accounts.google.com/gsi/client";
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => {
      scriptPromise = null;
      reject(new Error("Couldn't load Google sign-in. Check your connection or ad blocker."));
    };
    document.head.appendChild(s);
  });
  return scriptPromise;
}

/** Preloads Google sign-in so the popup can open straight from the next click */
export function preloadDrive() {
  if (driveAvailable() && typeof window !== "undefined") loadScript().catch(() => {});
}

export const driveConnected = () => !!token && token.expiresAt - Date.now() > 60_000;

/**
 * Asks the candidate to allow Drive access (Google's popup). Call it from a click handler, or browsers block
 * the popup. Resolves once access is granted; rejects if it is refused or the popup is closed.
 */
export async function connectDrive(): Promise<void> {
  if (!driveAvailable()) throw new Error("Google Drive isn't set up for this site (NEXT_PUBLIC_GOOGLE_CLIENT_ID).");
  if (driveConnected()) return;
  await loadScript();
  await new Promise<void>((resolve, reject) => {
    const client = window.google!.accounts.oauth2.initTokenClient({
      client_id: driveClientId,
      scope: SCOPE,
      callback: (resp) => {
        if (resp.error || !resp.access_token) {
          reject(new Error(resp.error_description || resp.error || "Google Drive access wasn't granted."));
          return;
        }
        token = { value: resp.access_token, expiresAt: Date.now() + (resp.expires_in ?? 3600) * 1000 };
        resolve();
      },
      error_callback: (err) =>
        reject(new Error(err.type === "popup_closed" ? "The Google window was closed." : err.message || "Google sign-in failed.")),
    });
    client.requestAccessToken({ prompt: token ? "" : undefined });
  });
}

async function driveFetch(url: string, init: RequestInit = {}) {
  if (!token) throw new Error("Not connected to Google Drive.");
  const res = await fetch(url, { ...init, headers: { ...(init.headers || {}), Authorization: `Bearer ${token.value}` } });
  if (res.status === 401) {
    token = null;
    throw new Error("Google Drive access expired. Connect again to save the recording.");
  }
  return res;
}

/** The app's "Skillaro Interviews" folder (drive.file only sees folders this app created) */
async function folderId(): Promise<string> {
  const q = encodeURIComponent(
    `name='${FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false`
  );
  const found = await driveFetch(`https://www.googleapis.com/drive/v3/files?q=${q}&fields=files(id)&spaces=drive`);
  if (found.ok) {
    const id = (await found.json()).files?.[0]?.id;
    if (id) return id;
  }
  const created = await driveFetch("https://www.googleapis.com/drive/v3/files?fields=id", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: FOLDER_NAME, mimeType: "application/vnd.google-apps.folder" }),
  });
  if (!created.ok) throw new Error(`Couldn't create the Drive folder (${created.status}).`);
  return (await created.json()).id;
}

export interface DriveFile {
  id: string;
  name: string;
  webViewLink?: string;
}

/** Uploads in 8 MB pieces (resumable upload), reporting progress 0-1 */
export async function uploadToDrive(
  blob: Blob,
  name: string,
  description: string,
  onProgress?: (fraction: number) => void
): Promise<DriveFile> {
  const parent = await folderId();
  const start = await driveFetch(
    "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id,name,webViewLink",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": blob.type || "video/webm",
        "X-Upload-Content-Length": String(blob.size),
      },
      body: JSON.stringify({ name, description, parents: [parent], mimeType: blob.type || "video/webm" }),
    }
  );
  const session = start.headers.get("Location");
  if (!start.ok || !session) throw new Error(`Google Drive refused the upload (${start.status}).`);

  let offset = 0;
  for (;;) {
    const end = Math.min(offset + CHUNK, blob.size);
    const res = await driveFetch(session, {
      method: "PUT",
      headers: { "Content-Range": `bytes ${offset}-${end - 1}/${blob.size}` },
      body: blob.slice(offset, end),
    });
    if (res.status === 200 || res.status === 201) {
      onProgress?.(1);
      return res.json();
    }
    if (res.status !== 308) throw new Error(`Upload failed (${res.status}). You can still download the recording.`);
    const range = res.headers.get("Range"); // e.g. "bytes=0-8388607"
    offset = range ? Number(range.split("-")[1]) + 1 : end;
    onProgress?.(offset / blob.size);
  }
}
