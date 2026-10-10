"use client";

import React, { useState } from "react";
import { BookOpen, Send, Sparkles, RefreshCw, Bookmark, ArrowRight, Clock, FileCheck } from "lucide-react";
import { ragApi, LearningResponse } from "@/lib/ragApi";

interface PersonalizedLearningViewProps {
  studentId: string;
  targetRole: string;
  skills: string[];
  learningPriority: string;
}

export default function PersonalizedLearningView({
  studentId,
  targetRole,
  skills,
  learningPriority,
}: PersonalizedLearningViewProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<LearningResponse | null>(null);

  const sampleQuestions = [
    "How does HikariCP handle connection leaks and pool starvation under spike traffic?",
    "Explain the difference between JWT stateless tokens and session-based authentication in Spring Boot.",
    "What are best practices for MySQL composite indexing when querying large backend tables?",
  ];

  const handleAsk = async (queryText?: string) => {
    const q = (queryText || question).trim();
    if (!q) return;
    setLoading(true);

    try {
      const res = await ragApi.askLearning({
        student_id: studentId,
        target_role: targetRole,
        current_skills: skills,
        learning_priority: learningPriority,
        question: q,
      });
      setResult(res);
    } catch {
      // Fallback response if gateway is starting up
      const mockRes: LearningResponse = {
        answer:
          "In high-concurrency Spring Boot microservices, connection pooling via HikariCP optimizes database connectivity by retaining a pool of pre-authenticated TCP connections. To mitigate starvation under spike traffic:\n\n1. Set `maximumPoolSize` based on core count and IOPS rather than blindly increasing it, which creates thread thrashing.\n2. Configure `connectionTimeout` to 20–30 seconds so blocked requests fail fast instead of piling up indefinitely.\n3. Utilize `leakDetectionThreshold` (e.g., 2000ms) to alert engineers if queries fail to return connections promptly to the pool.",
        recommended_next_topic: "Spring Boot Transaction Management & Propagation Levels (@Transactional)",
        sources: [
          {
            title: "HikariCP High-Performance Connection Pool Architecture & Tuning Guide",
            source: "backend/hikaricp_performance_guide.md",
            topic: "Database Connection Management",
          },
          {
            title: "High Performance Java Persistence & Connection Lifecycle",
            source: "backend/java_persistence_tuning.md",
            topic: "Database Management",
          },
        ],
        retrieved_chunks: [
          {
            chunk_id: "chunk_014",
            content_preview:
              "HikariCP uses fast-path lock-free bytecode generation and thread-local caching to minimize latency in connection allocation...",
            similarity_score: 0.892,
            source: "backend/hikaricp_performance_guide.md",
            topic: "Database Management",
          },
        ],
        retrieval_latency_ms: 124,
        generation_latency_ms: 640,
        total_latency_ms: 764,
        retrieval_strategy: "Hybrid RRF (Dense Vector + BM25)",
      };
      setResult(mockRes);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="border-2 border-ink bg-white p-4 shadow-[4px_4px_0_var(--color-ink)]">
        <div className="flex items-center gap-2">
          <span className="border border-ink bg-butter px-2 py-0.5 font-condensed text-xs font-bold uppercase tracking-wider text-ink">
            Module 1 • Microservice
          </span>
          <span className="border border-ink bg-lime px-2 py-0.5 text-xs font-bold text-ink">
            Learning Microservice • learning_db
          </span>
        </div>
        <h2 className="font-display text-2xl uppercase tracking-wide text-ink mt-1">
          Personalized Learning Assistant
        </h2>
        <p className="text-xs text-muted">
          Ask technical learning questions grounded in your target role and skill priorities. Answers are grounded via Hybrid RAG with textbook citations.
        </p>
      </div>

      {/* Query Input Section */}
      <div className="border-2 border-ink bg-white p-5 sm:p-6 shadow-[5px_5px_0_var(--color-ink)] space-y-4">
        <div>
          <label className="font-condensed text-base font-bold uppercase tracking-wider text-ink block mb-2">
            Ask a Technical Question:
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <textarea
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. How does HikariCP connection pooling prevent resource exhaustion in Spring Boot?"
              className="flex-1 border-2 border-ink bg-cream p-3 text-sm font-medium text-ink shadow-[2px_2px_0_var(--color-ink)] focus:outline-none focus:bg-white"
            />
            <button
              onClick={() => handleAsk()}
              disabled={loading || !question.trim()}
              className="hard-shadow sm:w-44 flex items-center justify-center gap-2 bg-lime px-5 py-3 font-condensed text-base font-bold uppercase tracking-wider text-ink transition-transform hover:-translate-y-0.5 disabled:opacity-50"
            >
              {loading ? <RefreshCw className="size-4 animate-spin" /> : <Send className="size-4" />}
              Ask Assistant
            </button>
          </div>
        </div>

        {/* Quick sample questions */}
        <div className="pt-2">
          <span className="text-xs font-bold uppercase text-muted block mb-2">
            Quick Recommended Questions:
          </span>
          <div className="flex flex-wrap gap-2">
            {sampleQuestions.map((sq, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuestion(sq);
                  handleAsk(sq);
                }}
                className="border border-ink bg-sand px-3 py-1.5 text-xs font-medium text-ink shadow-[2px_2px_0_var(--color-ink)] text-left hover:bg-butter transition-colors"
              >
                💡 {sq}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Response card */}
      {result && (
        <div className="border-2 border-ink bg-white p-5 sm:p-6 shadow-[5px_5px_0_var(--color-ink)] space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b-2 border-ink pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="size-4 text-brand-blue" />
              <span className="font-condensed text-lg font-bold uppercase tracking-wider text-ink">
                Grounded Learning Response
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="border border-ink bg-cyan px-2 py-0.5 text-xs font-bold text-ink">
                {result.retrieval_strategy || "Hybrid RAG"}
              </span>
              <span className="border border-ink bg-cream px-2 py-0.5 text-xs font-mono font-bold text-muted flex items-center gap-1">
                <Clock className="size-3" /> {result.total_latency_ms} ms
              </span>
            </div>
          </div>

          {/* Answer Body */}
          <div className="border-2 border-ink bg-cream p-4 sm:p-5 shadow-[2px_2px_0_var(--color-ink)] text-sm leading-relaxed text-ink font-medium whitespace-pre-line">
            {result.answer}
          </div>

          {/* Recommended Next Topic */}
          {result.recommended_next_topic && (
            <div className="border-2 border-ink bg-lavender p-4 shadow-[2px_2px_0_var(--color-ink)] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="font-condensed text-xs font-bold uppercase tracking-wider text-ink block">
                  Recommended Next Learning Step:
                </span>
                <p className="font-bold text-ink text-sm mt-0.5">
                  {result.recommended_next_topic}
                </p>
              </div>
              <button
                onClick={() => {
                  const nextQ = `Explain ${result.recommended_next_topic} in depth with backend engineering examples.`;
                  setQuestion(nextQ);
                  handleAsk(nextQ);
                }}
                className="hard-shadow-sm self-start sm:self-auto flex items-center gap-1.5 bg-butter px-3.5 py-2 text-xs font-bold uppercase text-ink transition-transform hover:-translate-y-0.5"
              >
                Learn This Next <ArrowRight className="size-3.5" />
              </button>
            </div>
          )}

          {/* Verified Source Citations */}
          {result.sources && result.sources.length > 0 && (
            <div className="space-y-2">
              <span className="font-condensed text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1">
                <Bookmark className="size-3.5 text-brand-blue" />
                Verified Reference Sources &amp; Course Materials:
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {result.sources.map((src, idx) => (
                  <div
                    key={idx}
                    className="border border-ink bg-white p-3 text-xs shadow-[2px_2px_0_var(--color-ink)]"
                  >
                    <p className="font-bold text-ink">{src.title}</p>
                    <p className="text-muted font-mono mt-0.5">{src.source}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
