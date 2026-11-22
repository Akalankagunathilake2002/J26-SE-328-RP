"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { CircleDot, Download, ExternalLink, Loader2, UploadCloud, AlertCircle, CheckCircle2 } from "lucide-react";
import { connectDrive, driveAvailable, driveConnected, uploadToDrive, type DriveFile } from "@/lib/googleDrive";
import type { Recording } from "@/lib/interviewRecorder";

interface RecordingPanelProps {
  recording: Recording | null;
  /** Still finishing the file */
  finalising: boolean;
  /** Upload straight away (Drive access was granted at the start) */
  autoUpload: boolean;
  fileName: string;
  description: string;
  /** Why parts are missing, e.g. the microphone couldn't be recorded */
  note?: string;
}

const size = (bytes: number) => `${(bytes / 1024 / 1024).toFixed(1)} MB`;

/** The finished recording: saved to the candidate's Google Drive, or downloaded */
export default function RecordingPanel({ recording, finalising, autoUpload, fileName, description, note }: RecordingPanelProps) {
  const [progress, setProgress] = useState<number | null>(null);
  const [file, setFile] = useState<DriveFile | null>(null);
  const [error, setError] = useState("");
  const startedRef = useRef(false);
  const url = useMemo(() => (recording ? URL.createObjectURL(recording.blob) : null), [recording]);
  useEffect(() => () => void (url && URL.revokeObjectURL(url)), [url]);

  const name = recording ? `${fileName}.${recording.extension}` : fileName;

  const upload = async (fromClick: boolean) => {
    if (!recording) return;
    setError("");
    try {
      if (fromClick) await connectDrive(); // may open Google's window; only allowed from a click
      setProgress(0);
      setFile(await uploadToDrive(recording.blob, name, description, setProgress));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setProgress(null);
    }
  };

  useEffect(() => {
    if (recording && autoUpload && driveConnected() && !startedRef.current) {
      startedRef.current = true;
      upload(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recording, autoUpload]);

  return (
    <section className="space-y-3 border-2 border-ink bg-white p-5 shadow-[5px_5px_0_var(--color-ink)]">
      <h3 className="flex items-center gap-2 font-condensed text-lg font-bold uppercase tracking-wider text-ink">
        <CircleDot className="size-5 text-pink" /> Interview recording
      </h3>
      {finalising && (
        <p className="flex items-center gap-2 text-sm text-muted">
          <Loader2 className="size-4 animate-spin" /> Finishing the recording…
        </p>
      )}
      {!finalising && !recording && <p className="text-sm text-muted">Nothing was recorded.</p>}
      {recording && url && (
        <>
          <video src={url} controls playsInline className="w-full max-w-3xl border-2 border-ink bg-black" />
          <p className="text-xs text-muted">
            {Math.floor(recording.seconds / 60)} min {recording.seconds % 60} s · {size(recording.blob.size)}
            {note ? ` · ${note}` : ""}
          </p>
          <div className="flex flex-wrap items-center gap-2">
            {driveAvailable() &&
              (file ? (
                <a
                  href={file.webViewLink || "https://drive.google.com/drive/my-drive"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hard-shadow-sm flex items-center gap-1.5 bg-lime px-3.5 py-2 text-xs font-bold uppercase text-ink"
                >
                  <CheckCircle2 className="size-4" /> Saved to Google Drive <ExternalLink className="size-3.5" />
                </a>
              ) : (
                <button
                  onClick={() => upload(true)}
                  disabled={progress != null}
                  className="hard-shadow-sm flex items-center gap-1.5 bg-butter px-3.5 py-2 text-xs font-bold uppercase text-ink disabled:opacity-60"
                >
                  {progress != null ? <Loader2 className="size-4 animate-spin" /> : <UploadCloud className="size-4" />}
                  {progress != null ? `Uploading ${Math.round(progress * 100)}%` : "Save to Google Drive"}
                </button>
              ))}
            <a
              href={url}
              download={name}
              className="flex items-center gap-1.5 border-2 border-ink bg-white px-3.5 py-2 text-xs font-bold uppercase text-ink hover:bg-cream"
            >
              <Download className="size-4" /> Download
            </a>
          </div>
          {progress != null && (
            <div className="h-2 w-full max-w-3xl border border-ink bg-cream">
              <div className="h-full bg-lime transition-all" style={{ width: `${progress * 100}%` }} />
            </div>
          )}
          {error && (
            <p className="flex items-center gap-1.5 text-xs font-bold text-ink">
              <AlertCircle className="size-3.5" /> {error}
            </p>
          )}
          <p className="text-[11px] text-muted">
            The recording is only in this browser tab until you save it. Leaving the page discards it.
          </p>
        </>
      )}
    </section>
  );
}
