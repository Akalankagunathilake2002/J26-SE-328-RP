"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  Send,
  Square,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Award,
  ArrowRight,
  FileText,
  PhoneOff,
  Eye,
  Smile,
  Gauge,
  MessageSquare,
} from "lucide-react";
import AIInterviewerAvatar from "./AIInterviewerAvatar";
import CandidateWebcam from "./CandidateWebcam";
import InterviewReport from "./InterviewReport";
import { useDeliveryAnalysis, type DeliveryMetrics } from "./useDeliveryAnalysis";
import type { InterviewProfile } from "./InterviewSetup";
import {
  ragApi,
  type InterviewSession,
  type InterviewQuestionResponse,
  type EvaluationResponse,
  type DeliveryTelemetry,
  type InterviewReport as Report,
} from "@/lib/ragApi";

interface InterviewStudioProps {
  studentId: string;
  profile: InterviewProfile;
  /** Back to setup for a new interview */
  onExit: () => void;
}

const SILENCE_RMS = 0.015; // mic level below which a 100 ms slice counts as a pause

export default function InterviewStudio({ studentId, profile, onExit }: InterviewStudioProps) {
  const { role: targetRole, level, skills, summary } = profile;
  const studentName = profile.name || "Candidate";

  const [session, setSession] = useState<InterviewSession | null>(null);
  const [questionData, setQuestionData] = useState<InterviewQuestionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [nextLoading, setNextLoading] = useState(false);
  const [interviewState, setInterviewState] = useState<"idle" | "speaking" | "listening" | "thinking">("idle");

  // Candidate controls
  const [videoOn, setVideoOn] = useState(true);
  const [micOn, setMicOn] = useState(true);
  const [videoEl, setVideoEl] = useState<HTMLVideoElement | null>(null);
  const analysis = useDeliveryAnalysis(videoEl, profile.analysisConsent && videoOn);

  // Answer recording
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [transcribing, setTranscribing] = useState(false);
  const [recordedDuration, setRecordedDuration] = useState<number>(0);
  const [waitingForMic, setWaitingForMic] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const activeMsRef = useRef(0);                 // speaking time excluding muted pauses
  const segmentStartRef = useRef(0);
  const levelRef = useRef<{ ctx: AudioContext; timer?: ReturnType<typeof setInterval>; quiet: number; total: number } | null>(null);
  const discardRecordingRef = useRef(false);

  // Evaluation
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [answerError, setAnswerError] = useState("");
  const [evaluationError, setEvaluationError] = useState("");
  const pendingDeliveryRef = useRef<DeliveryTelemetry>({});
  const [deliveryByTurn, setDeliveryByTurn] = useState<Record<string, DeliveryTelemetry>>({});

  // End of interview
  const [report, setReport] = useState<Report | null>(null);
  const [ending, setEnding] = useState(false);
  const endedRef = useRef(false);

  // The interviewer avatar is the single voice source. It speaks either the question or, after an
  // answer, its spoken feedback; bumping speakRequest asks it to speak `speech`.
  const [speakRequest, setSpeakRequest] = useState(0);
  const [speech, setSpeech] = useState<{ text: string; jobIds: string[]; kind: "question" | "feedback" }>({
    text: "",
    jobIds: [],
    kind: "question",
  });
  const sayAsInterviewer = (text: string, kind: "question" | "feedback", jobIds: string[] = []) => {
    setSpeech({ text, kind, jobIds });
    setSpeakRequest((n) => n + 1);
  };
  const speakQuestion = (q: InterviewQuestionResponse) => sayAsInterviewer(q.question, "question", q.avatar_job_ids ?? []);

  // Hands-free prefetch: the next question is requested as soon as an answer is evaluated, so its
  // video renders while the interviewer gives feedback and it can start the moment she finishes.
  const prefetchRef = useRef<Promise<InterviewQuestionResponse | null> | null>(null);
  const discardPrefetch = () => {
    const stale = prefetchRef.current;
    prefetchRef.current = null;
    stale
      ?.then((q) => {
        if (q?.avatar_job_ids?.length) return ragApi.cancelAvatarClips(q.avatar_job_ids);
      })
      .catch(() => {});
  };

  // Hands-free: the mic opens when the question ends, Submit Answer evaluates straight away, and the
  // next question follows the interviewer's spoken feedback, like a real interview.
  const [handsFree, setHandsFree] = useState(true);
  const handsFreeRef = useRef(handsFree);
  const handleEvaluateRef = useRef<((answer?: string, spokenSeconds?: number) => Promise<void>) | null>(null);
  const startRecordingRef = useRef<(() => Promise<void>) | null>(null);

  const questionContext = (prev?: { question: string; answer: string; missing: string[] }) => ({
    candidate_background: summary || undefined,
    ...(prev && {
      previous_question: prev.question,
      previous_answer: prev.answer,
      previous_missing_concepts: prev.missing,
    }),
  });

  const handleSpeechEnd = () => {
    setInterviewState((s) => (s === "speaking" ? "idle" : s));
    if (!handsFree || endedRef.current) return;
    if (speech.kind === "question" && !isRecording && !transcript.trim() && !evaluation) {
      if (micOn) startRecording();
      else setWaitingForMic(true);                 // starts as soon as the candidate unmutes
    } else if (speech.kind === "feedback") {
      setTimeout(() => !endedRef.current && handleNextQuestion(), 1200);
    }
  };

  // ---------------------------------------------------------------- session
  const resetAnswer = () => {
    setTranscript("");
    setEvaluation(null);
    setAnswerError("");
    setEvaluationError("");
    setRecordedDuration(0);
    setWaitingForMic(false);
    pendingDeliveryRef.current = {};
  };

  const handleStartSession = async () => {
    setLoading(true);
    try {
      const sess = await ragApi.startInterview(studentId, targetRole, level, skills);
      setSession(sess);
      discardPrefetch();
      const q = await ragApi.getInterviewQuestion(sess.session_id, studentId, targetRole, level, skills, questionContext());
      setQuestionData({ ...q, question_number: 1 });
      resetAnswer();
      speakQuestion(q);
    } catch (err) {
      console.warn("Couldn't start the interview:", err);
      setAnswerError(
        `${err instanceof Error ? err.message : "The interview service is unreachable."} Check that the backend is running, then try again.`
      );
    } finally {
      setLoading(false);
    }
  };

  const startedRef = useRef(false);
  useEffect(() => {
    // Once per mount, even under React Strict Mode's double effect
    if (startedRef.current) return;
    startedRef.current = true;
    handleStartSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleNextQuestion = async () => {
    if (!session || endedRef.current) return;
    setNextLoading(true);
    try {
      // Prefetched during the interviewer's feedback (hands-free), so usually already rendering
      const prefetched = prefetchRef.current ? await prefetchRef.current : null;
      prefetchRef.current = null;
      const prev =
        questionData && transcript.trim()
          ? { question: questionData.question, answer: transcript.trim(), missing: evaluation?.missing_concepts ?? [] }
          : undefined;
      const q =
        prefetched ??
        (await ragApi.getInterviewQuestion(session.session_id, studentId, targetRole, level, skills, questionContext(prev)));
      if (endedRef.current) return;
      setQuestionData({ ...q, question_number: (questionData?.question_number || 1) + 1 });
      resetAnswer();
      speakQuestion(q);
    } catch (err) {
      setAnswerError(`${err instanceof Error ? err.message : "Couldn't get the next question."} Try Next question again.`);
    } finally {
      setNextLoading(false);
    }
  };

  // ---------------------------------------------------------------- recording
  const stopLevelMeter = () => {
    const m = levelRef.current;
    levelRef.current = null;
    if (!m) return null;
    clearInterval(m.timer);
    m.ctx.close().catch(() => {});
    return m.total ? m.quiet / m.total : null;
  };

  const startRecording = async () => {
    if (!micOn) {
      setWaitingForMic(true);
      return;
    }
    setWaitingForMic(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Chrome/Firefox record WebM/Opus, Safari MP4/AAC; use whatever this browser supports
      const preferred = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
      const mimeType = preferred.find((t) => typeof MediaRecorder.isTypeSupported === "function" && MediaRecorder.isTypeSupported(t));
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];
      activeMsRef.current = 0;
      segmentStartRef.current = Date.now();
      discardRecordingRef.current = false;

      // Pauses: share of 100 ms slices (while unmuted) that were near-silent
      try {
        const ctx = new AudioContext();
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 1024;
        ctx.createMediaStreamSource(stream).connect(analyser);
        const buf = new Float32Array(analyser.fftSize);
        const meter: { ctx: AudioContext; timer?: ReturnType<typeof setInterval>; quiet: number; total: number } =
          { ctx, quiet: 0, total: 0 };
        meter.timer = setInterval(() => {
          if (recorder.state !== "recording") return;       // muted slices don't count as pauses
          analyser.getFloatTimeDomainData(buf);
          const rms = Math.sqrt(buf.reduce((a, v) => a + v * v, 0) / buf.length);
          meter.total++;
          if (rms < SILENCE_RMS) meter.quiet++;
        }, 100);
        levelRef.current = meter;
      } catch {
        levelRef.current = null;
      }

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      recorder.onstop = async () => {
        if (recorder.state !== "inactive") return;
        const pauseRatio = stopLevelMeter();
        const camera: DeliveryMetrics | null = analysis.stopCollecting();
        stream.getTracks().forEach((track) => track.stop());
        if (discardRecordingRef.current) return;      // interview ended mid-answer

        const durationSec = Math.max(1, Math.round(activeMsRef.current / 1000));
        setRecordedDuration(durationSec);
        pendingDeliveryRef.current = {
          pause_ratio: pauseRatio == null ? undefined : Math.round(pauseRatio * 100) / 100,
          ...(camera && {
            face_visible_ratio: camera.face_visible_ratio,
            eye_contact_ratio: camera.eye_contact_ratio ?? undefined,
            smile_ratio: camera.smile_ratio ?? undefined,
            brow_tension_ratio: camera.brow_tension_ratio ?? undefined,
            blink_rate_per_min: camera.blink_rate_per_min ?? undefined,
            head_steadiness: camera.head_steadiness ?? undefined,
          }),
        };

        const recordedType = recorder.mimeType || "audio/webm";
        const audioBlob = new Blob(audioChunksRef.current, { type: recordedType.split(";")[0] });
        setTranscribing(true);
        try {
          const res = await ragApi.transcribeAudio(audioBlob);
          setTranscript(res.transcript);
          // Hands-free: Submit Answer goes straight to evaluation
          if (handsFreeRef.current) handleEvaluateRef.current?.(res.transcript, durationSec);
        } catch (err) {
          // Never put words in the candidate's mouth: the transcript is what gets scored
          setAnswerError(
            `${err instanceof Error ? err.message : "Transcription failed."} Your recording wasn't transcribed. Record again or type your answer.`
          );
        } finally {
          setTranscribing(false);
          setInterviewState("idle");
        }
      };

      recorder.start();
      analysis.startCollecting();
      setAnswerError("");
      setIsRecording(true);
      setInterviewState("listening");
    } catch (err) {
      console.warn("Microphone unavailable:", err);
      setIsRecording(false);
      setInterviewState("idle");
      setAnswerError(
        "Microphone access was blocked or no microphone was found. Allow microphone access in your browser, or type your answer below."
      );
    }
  };

  /** Submit Answer (hands-free) / Stop recording (manual) */
  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      if (recorder.state === "recording") activeMsRef.current += Date.now() - segmentStartRef.current;
      recorder.stop();
    }
    setIsRecording(false);
  };

  // Mic toggle: muting pauses the answer recording; unmuting resumes it (or starts a pending one)
  const toggleMic = () => {
    const next = !micOn;
    setMicOn(next);
    const recorder = mediaRecorderRef.current;
    if (recorder && isRecording) {
      if (!next && recorder.state === "recording") {
        activeMsRef.current += Date.now() - segmentStartRef.current;
        recorder.pause();
      } else if (next && recorder.state === "paused") {
        segmentStartRef.current = Date.now();
        recorder.resume();
      }
    }
  };

  useEffect(() => {
    // Hands-free question ended while muted: start the answer the moment the mic comes back
    if (micOn && waitingForMic && !isRecording && !endedRef.current) startRecordingRef.current?.();
  }, [micOn, waitingForMic, isRecording]);

  // ---------------------------------------------------------------- evaluation
  const handleEvaluate = async (answer: string = transcript, spokenSeconds: number = recordedDuration) => {
    if (!questionData || !answer.trim() || endedRef.current) return;
    setEvaluating(true);
    setEvaluationError("");
    setInterviewState("thinking");

    // Only measured values: pace needs a real recording; camera cues only if the candidate opted in
    const words = answer.trim().split(/\s+/).length;
    const fillers = (answer.match(/\b(um+|uh+|erm+|hmm+|you know|i mean)\b/gi) || []).length;
    const telemetry: DeliveryTelemetry = {
      filler_words_count: fillers,
      ...(spokenSeconds > 0 && {
        speaking_duration_seconds: spokenSeconds,
        words_per_minute: Math.round(words / (spokenSeconds / 60)),
      }),
      ...pendingDeliveryRef.current,
    };

    try {
      const res = await ragApi.evaluateAnswer(questionData.turn_id, answer, studentId, telemetry);
      if (endedRef.current) return;
      setEvaluation(res);
      setDeliveryByTurn((d) => ({ ...d, [questionData.turn_id]: telemetry }));
      // The interviewer reacts out loud, as in a real interview (rendered on the avatar)
      if (res.spoken_feedback) sayAsInterviewer(res.spoken_feedback, "feedback", res.avatar_job_ids ?? []);
      // Ask for the follow-up question now: its clips queue right behind the feedback clips
      if (handsFreeRef.current && session) {
        discardPrefetch();
        prefetchRef.current = ragApi
          .getInterviewQuestion(session.session_id, studentId, targetRole, level, skills,
            questionContext({ question: questionData.question, answer: answer.trim(), missing: res.missing_concepts ?? [] }))
          .catch(() => null);
      }
    } catch (err) {
      // No made-up scores: a fabricated 4.8/5 would mislead the candidate about their readiness
      setEvaluation(null);
      setEvaluationError(
        `${err instanceof Error ? err.message : "Evaluation failed."} Your answer is kept. Try evaluating again in a moment.`
      );
    } finally {
      setEvaluating(false);
      setInterviewState("idle");
    }
  };

  useEffect(() => {
    handsFreeRef.current = handsFree;
    handleEvaluateRef.current = handleEvaluate;
    startRecordingRef.current = startRecording;
  });

  // ---------------------------------------------------------------- end
  const handleEnd = async () => {
    if (!session || ending) return;
    if (!window.confirm("End the interview and see your report?")) return;
    endedRef.current = true;
    setEnding(true);
    discardRecordingRef.current = true;
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") mediaRecorderRef.current.stop();
    setIsRecording(false);
    stopLevelMeter();
    analysis.stopCollecting();
    discardPrefetch();
    try {
      setReport(await ragApi.endInterview(session.session_id));
    } catch (err) {
      setAnswerError(`${err instanceof Error ? err.message : "Couldn't load the report."}`);
      endedRef.current = false;
    } finally {
      setEnding(false);
    }
  };

  useEffect(() => () => {
    // Leaving the page mid-answer: release the mic
    discardRecordingRef.current = true;
    const r = mediaRecorderRef.current;
    if (r && r.state !== "inactive") r.stop();
  }, []);

  if (report) {
    return <InterviewReport report={report} role={targetRole} level={level} delivery={deliveryByTurn} onRestart={onExit} />;
  }

  const current = questionData ? deliveryByTurn[questionData.turn_id] : undefined;
  const pct = (x?: number) => (x == null ? null : `${Math.round(x * 100)}%`);

  return (
    <div className="space-y-6">
      {/* Studio header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-2 border-ink bg-white p-4 shadow-[4px_4px_0_var(--color-ink)]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="border border-ink bg-pink px-2 py-0.5 font-condensed text-xs font-bold uppercase tracking-wider text-ink">
              {targetRole}
            </span>
            <span className="border border-ink bg-lime px-2 py-0.5 text-xs font-bold text-ink">{level}</span>
            {profile.analysisConsent && (
              <span className="border border-ink bg-cyan px-2 py-0.5 text-xs font-bold text-ink">Delivery analysis on</span>
            )}
          </div>
          <h2 className="font-display text-2xl uppercase tracking-wide text-ink mt-1">AI Mock Interview Studio</h2>
          <p className="text-xs text-muted">Face-to-face technical interview with Elena Vance (AI Lead Interviewer).</p>
        </div>
        {!handsFree && session && (
          <button
            onClick={handleNextQuestion}
            disabled={nextLoading || evaluating || isRecording}
            className="hard-shadow flex items-center gap-2 bg-butter px-4 py-2.5 font-condensed text-sm font-bold uppercase tracking-wider text-ink transition-transform hover:-translate-y-0.5 disabled:opacity-50"
          >
            {nextLoading ? <RefreshCw className="size-4 animate-spin" /> : <ArrowRight className="size-4" />}
            Next question
          </button>
        )}
      </div>

      {loading && !questionData && (
        <div className="flex items-center justify-center gap-2 border-2 border-ink bg-cream p-10 text-sm font-bold text-ink shadow-[5px_5px_0_var(--color-ink)]">
          <RefreshCw className="size-4 animate-spin" /> Elena is preparing your first question…
        </div>
      )}

      {!loading && !questionData && answerError && (
        <div className="space-y-3 border-2 border-ink bg-pink/40 p-5 text-sm font-bold text-ink">
          <p className="flex items-start gap-2"><AlertCircle className="size-4 shrink-0" /> {answerError}</p>
          <div className="flex gap-2">
            <button onClick={handleStartSession} className="hard-shadow-sm bg-lime px-4 py-2 text-xs font-bold uppercase">Try again</button>
            <button onClick={onExit} className="hard-shadow-sm bg-white px-4 py-2 text-xs font-bold uppercase">Back to setup</button>
          </div>
        </div>
      )}

      {session && questionData && (
        <div className="space-y-6">
          {/* Interviewer + candidate */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <AIInterviewerAvatar
              currentTextToSpeak={speech.text || questionData.question}
              speakRequest={speakRequest}
              avatarJobIds={speech.jobIds}
              interviewState={interviewState}
              onSpeechEnd={handleSpeechEnd}
              onSpeechStart={() => setInterviewState("speaking")}
              topic={questionData.topic}
              difficulty={questionData.difficulty}
            />
            <CandidateWebcam
              candidateName={`${studentName} (Candidate)`}
              candidateId={studentId}
              isRecordingAnswer={isRecording}
              videoOn={videoOn}
              micOn={micOn}
              onVideoElement={setVideoEl}
              analysisStatus={profile.analysisConsent ? analysis.status : "off"}
              liveCues={analysis.live}
            />
          </div>

          {/* Candidate controls */}
          <div className="flex flex-wrap items-center justify-center gap-3 border-2 border-ink bg-white p-3 shadow-[4px_4px_0_var(--color-ink)]">
            <button
              onClick={() => setVideoOn(!videoOn)}
              aria-pressed={videoOn}
              className={`hard-shadow-sm flex items-center gap-2 px-4 py-2.5 text-xs font-bold uppercase text-ink transition-transform hover:-translate-y-0.5 ${videoOn ? "bg-white" : "bg-pink"}`}
            >
              {videoOn ? <Video className="size-4" /> : <VideoOff className="size-4" />}
              {videoOn ? "Camera on" : "Camera off"}
            </button>
            <button
              onClick={toggleMic}
              aria-pressed={micOn}
              className={`hard-shadow-sm flex items-center gap-2 px-4 py-2.5 text-xs font-bold uppercase text-ink transition-transform hover:-translate-y-0.5 ${micOn ? "bg-white" : "bg-pink"}`}
            >
              {micOn ? <Mic className="size-4" /> : <MicOff className="size-4" />}
              {micOn ? "Mic on" : "Mic muted"}
            </button>

            {isRecording ? (
              <button
                onClick={stopRecording}
                className="hard-shadow flex items-center gap-2 bg-lime px-6 py-2.5 font-condensed text-sm font-bold uppercase tracking-wider text-ink transition-transform hover:-translate-y-0.5"
              >
                {handsFree ? <Send className="size-4" /> : <Square className="size-4" />}
                {handsFree ? "Submit answer" : "Stop recording"}
              </button>
            ) : (
              <button
                onClick={startRecording}
                disabled={transcribing || evaluating || interviewState === "speaking"}
                className="hard-shadow flex items-center gap-2 bg-sun px-6 py-2.5 font-condensed text-sm font-bold uppercase tracking-wider text-ink transition-transform hover:-translate-y-0.5 disabled:opacity-50"
              >
                <Mic className="size-4" /> {transcript.trim() ? "Answer again" : "Start answer"}
              </button>
            )}

            <button
              onClick={handleEnd}
              disabled={ending}
              className="hard-shadow-sm flex items-center gap-2 bg-pink px-4 py-2.5 text-xs font-bold uppercase text-ink transition-transform hover:-translate-y-0.5 disabled:opacity-50"
            >
              {ending ? <RefreshCw className="size-4 animate-spin" /> : <PhoneOff className="size-4" />}
              End interview
            </button>

            <label className="flex cursor-pointer items-center gap-1.5 border border-ink bg-cream px-2 py-1 text-xs font-bold text-ink">
              <input type="checkbox" checked={handsFree} onChange={(e) => setHandsFree(e.target.checked)} className="accent-brand-blue" />
              Hands-free
            </label>

            <p className="w-full text-center text-[11px] font-medium text-muted">
              {waitingForMic
                ? "Your mic is muted. Unmute to start answering."
                : transcribing
                ? "Transcribing your answer…"
                : evaluating
                ? "Elena is evaluating your answer…"
                : isRecording
                ? handsFree
                  ? "Speak your answer, then click Submit answer."
                  : "Speak your answer, then click Stop recording to review it."
                : handsFree
                ? "Your mic opens automatically when Elena finishes the question."
                : "Click Start answer, or type your answer below."}
            </p>
          </div>

          {/* Question & rubric */}
          <div className="border-2 border-ink bg-white p-5 sm:p-6 shadow-[5px_5px_0_var(--color-ink)] space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b-2 border-ink pb-3">
              <div className="flex items-center gap-2">
                <span className="border border-ink bg-sun px-2.5 py-1 text-xs font-bold text-ink">
                  Question #{questionData.question_number} • {questionData.topic}
                </span>
                <span className="border border-ink bg-lavender px-2 py-1 text-xs font-bold text-ink">
                  Difficulty: {questionData.difficulty}
                </span>
              </div>
              {questionData.context_or_reason && (
                <span className="text-xs font-medium italic text-muted">{questionData.context_or_reason}</span>
              )}
            </div>
            <div className="border-2 border-ink bg-cream p-4 shadow-[2px_2px_0_var(--color-ink)]">
              <span className="font-condensed text-xs font-bold uppercase tracking-wider text-muted block mb-1">
                Elena&apos;s Technical Question:
              </span>
              <p className="text-base sm:text-lg font-bold text-ink leading-relaxed">{questionData.question}</p>
            </div>
            {questionData.rubric_criteria && questionData.rubric_criteria.length > 0 && (
              <div className="border border-ink bg-sand/60 p-4 space-y-2">
                <span className="font-condensed text-xs font-bold uppercase tracking-wider text-ink block">
                  What a strong answer covers:
                </span>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  {questionData.rubric_criteria.map((crit, idx) => (
                    <div
                      key={idx}
                      className="border border-ink bg-white p-2.5 text-xs font-medium text-ink shadow-[2px_2px_0_var(--color-ink)] flex items-start gap-2"
                    >
                      <span className="size-2 rounded-full bg-brand-blue mt-1 shrink-0" />
                      <span>{crit}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Answer & feedback */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <div className="border-2 border-ink bg-white p-5 sm:p-6 shadow-[5px_5px_0_var(--color-ink)] space-y-4">
              <h3 className="border-b-2 border-ink pb-3 font-condensed text-lg font-bold uppercase tracking-wider text-ink flex items-center gap-2">
                <Mic className="size-4 text-brand-blue" /> Your answer
              </h3>

              {answerError && (
                <div className="flex items-start gap-2 border-2 border-ink bg-pink/40 p-3 text-xs font-bold text-ink">
                  <AlertCircle className="size-4 shrink-0" />
                  <span>{answerError}</span>
                </div>
              )}

              <div>
                <div className="flex items-center justify-between mb-1.5 text-xs font-semibold text-muted">
                  <label htmlFor="answer-transcript">Transcript (you can edit it before evaluating)</label>
                  <span>{transcript.length} characters</span>
                </div>
                <textarea
                  id="answer-transcript"
                  rows={5}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Your spoken answer appears here after you submit it, or type it…"
                  className="w-full border-2 border-ink bg-cream p-3 text-xs font-medium text-ink leading-relaxed shadow-[2px_2px_0_var(--color-ink)] focus:outline-none focus:bg-white"
                />
              </div>

              <button
                onClick={() => handleEvaluate()}
                disabled={evaluating || !transcript.trim() || !!evaluation}
                className="hard-shadow w-full flex items-center justify-center gap-2 bg-lime py-3 font-condensed text-sm font-bold uppercase tracking-wider text-ink transition-transform hover:-translate-y-0.5 disabled:opacity-50"
              >
                {evaluating ? (
                  <>
                    <RefreshCw className="size-4 animate-spin" /> Evaluating…
                  </>
                ) : (
                  <>
                    <Sparkles className="size-4" /> {evaluation ? "Evaluated" : "Evaluate answer"}
                  </>
                )}
              </button>

              {evaluationError && (
                <div className="flex items-start gap-2 border-2 border-ink bg-pink/40 p-3 text-xs font-bold text-ink">
                  <AlertCircle className="size-4 shrink-0" />
                  <span>{evaluationError}</span>
                </div>
              )}
            </div>

            <div className="border-2 border-ink bg-white p-5 sm:p-6 shadow-[5px_5px_0_var(--color-ink)] space-y-5">
              <div className="flex items-center justify-between border-b-2 border-ink pb-3">
                <h3 className="font-condensed text-lg font-bold uppercase tracking-wider text-ink flex items-center gap-2">
                  <Award className="size-4 text-brand-blue" /> Feedback
                </h3>
                {evaluation?.overall_score != null && (
                  <span className="border border-ink bg-butter px-2 py-0.5 text-xs font-bold text-ink">
                    Overall {evaluation.overall_score} / 5
                  </span>
                )}
              </div>

              {evaluation ? (
                <div className="space-y-4">
                  {evaluation.spoken_feedback && (
                    <div className="border-2 border-ink bg-cream p-3 shadow-[2px_2px_0_var(--color-ink)]">
                      <span className="font-condensed text-[11px] font-bold uppercase tracking-wider text-muted block mb-1">Elena says:</span>
                      <p className="text-sm font-semibold italic text-ink">&ldquo;{evaluation.spoken_feedback}&rdquo;</p>
                    </div>
                  )}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                    {([
                      ["Knowledge", evaluation.technical_accuracy],
                      ["Relevance", evaluation.relevance],
                      ["Explanation", evaluation.explanation_quality],
                      ["Clarity", evaluation.clarity],
                    ] as const).map(([label, value]) => (
                      <div key={label} className="border-2 border-ink bg-cream p-2.5 text-center shadow-[2px_2px_0_var(--color-ink)]">
                        <span className="text-[10px] font-bold uppercase text-muted block">{label}</span>
                        <span className="font-display text-2xl font-bold text-ink">{value}</span>
                        <span className="text-[10px] font-bold text-muted block">/ 5.0</span>
                      </div>
                    ))}
                  </div>

                  {/* Delivery: measured values only */}
                  {current && (
                    <div className="border border-ink bg-cyan/15 p-3 text-xs space-y-2">
                      <span className="font-bold text-ink uppercase text-[10px] tracking-wider font-condensed">Delivery (measured)</span>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {[
                          current.words_per_minute != null && { icon: MessageSquare, label: "Pace", value: `${current.words_per_minute} wpm` },
                          current.pause_ratio != null && { icon: Gauge, label: "Pauses", value: pct(current.pause_ratio) },
                          { icon: MessageSquare, label: "Fillers", value: String(current.filler_words_count ?? 0) },
                          current.eye_contact_ratio != null && { icon: Eye, label: "Eye contact", value: pct(current.eye_contact_ratio) },
                          current.smile_ratio != null && { icon: Smile, label: "Smiling", value: pct(current.smile_ratio) },
                          current.head_steadiness != null && { icon: Gauge, label: "Head steadiness", value: pct(current.head_steadiness) },
                        ]
                          .filter(Boolean)
                          .map((m) => {
                            const { icon: Icon, label, value } = m as { icon: typeof Eye; label: string; value: string | null };
                            return (
                              <div key={label} className="border border-ink bg-white p-1.5 text-center">
                                <span className="text-[9px] uppercase text-muted flex items-center justify-center gap-1 font-condensed">
                                  <Icon className="size-3" /> {label}
                                </span>
                                <span className="font-bold text-xs text-ink">{value}</span>
                              </div>
                            );
                          })}
                      </div>
                      {current.eye_contact_ratio == null && profile.analysisConsent && (
                        <p className="text-[10px] text-muted">Camera cues weren&apos;t available for this answer (camera off or face not detected).</p>
                      )}
                    </div>
                  )}

                  <div className="border border-ink bg-cream p-3 text-xs">
                    <span className="font-bold text-ink block mb-1">Technical assessment:</span>
                    <p className="text-muted leading-relaxed font-medium">{evaluation.technical_feedback}</p>
                  </div>
                  <div className="border border-ink bg-cream p-3 text-xs">
                    <span className="font-bold text-ink block mb-1">Communication &amp; delivery:</span>
                    <p className="text-muted leading-relaxed font-medium">{evaluation.communication_feedback}</p>
                  </div>

                  {evaluation.strengths && evaluation.strengths.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="text-xs font-bold uppercase text-ink flex items-center gap-1.5">
                        <CheckCircle2 className="size-3.5 text-brand-blue" /> Strengths:
                      </span>
                      {evaluation.strengths.map((str, idx) => (
                        <div key={idx} className="border border-ink bg-lime/30 p-2 text-xs font-medium text-ink shadow-[2px_2px_0_var(--color-ink)]">
                          ✓ {str}
                        </div>
                      ))}
                    </div>
                  )}
                  {evaluation.missing_concepts && evaluation.missing_concepts.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="text-xs font-bold uppercase text-ink flex items-center gap-1.5">
                        <AlertCircle className="size-3.5 text-pink" /> To cover next time:
                      </span>
                      {evaluation.missing_concepts.map((item, idx) => (
                        <div key={idx} className="border border-ink bg-sun/40 p-2 text-xs font-medium text-ink shadow-[2px_2px_0_var(--color-ink)]">
                          • {item}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center p-8 text-center space-y-2 border border-dashed border-ink/40 bg-sand/30">
                  <FileText className="size-8 text-muted" />
                  <p className="text-sm font-bold text-ink">No answer evaluated yet</p>
                  <p className="text-xs text-muted max-w-[280px]">
                    Answer the question and submit it; Elena&apos;s scores and feedback appear here.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
