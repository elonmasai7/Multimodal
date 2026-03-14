"use client";

import { useEffect, useMemo, useState } from "react";

import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import Link from "next/link";

import {
  getLessonPerformanceAnalytics,
  getLessonSessions,
  getQuizPerformanceAnalytics,
  getStudentProgressAnalytics,
} from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

type LessonSession = {
  lesson_id: string;
  prompt: string;
  duration: number | null;
  quiz_attempts: number;
  created_at: string;
};

type PerfRow = { lesson_id: string; average_score: number; completion_rate: number; attempts: number };
type ProgressRow = { user_id: string; lesson_id: string; score: number; completion: number; time_spent_seconds: number };
type QuizRow = { lesson_id: string; total_attempts: number; correct_count: number; correct_rate: number };

function fmtTime(seconds: number): string {
  if (seconds <= 0) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return "—";
  }
}

function WatchBar({ pctAll, pctHalf }: { pctAll: number; pctHalf: number }) {
  const pctSkip = Math.max(0, 100 - pctAll - pctHalf);
  return (
    <div className="space-y-1">
      <div className="flex h-2 overflow-hidden rounded-full bg-white/10">
        <div className="bg-emerald-400 transition-all" style={{ width: `${pctAll}%` }} title={`All: ${pctAll}%`} />
        <div className="bg-amber-400 transition-all" style={{ width: `${pctHalf}%` }} title={`Half: ${pctHalf}%`} />
        <div className="bg-red-400/60 transition-all" style={{ width: `${pctSkip}%` }} title={`Skipped: ${pctSkip}%`} />
      </div>
      <div className="flex gap-3 text-[10px] text-slate-400">
        <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />Watched all {pctAll}%</span>
        <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-amber-400" />Half {pctHalf}%</span>
        <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-red-400/60" />Skipped {pctSkip}%</span>
      </div>
    </div>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <article className="rounded-2xl border border-white/15 bg-white/5 p-4">
      <p className="text-xs uppercase tracking-[0.12em] text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-bold text-white">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
    </article>
  );
}

export default function TeacherPage() {
  const token = useAuthStore((s) => s.token);
  const [perf, setPerf] = useState<PerfRow[]>([]);
  const [sessions, setSessions] = useState<LessonSession[]>([]);
  const [progress, setProgress] = useState<ProgressRow[]>([]);
  const [quizPerf, setQuizPerf] = useState<QuizRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    Promise.all([
      getLessonPerformanceAnalytics(token),
      getLessonSessions(token),
      getStudentProgressAnalytics(token),
      getQuizPerformanceAnalytics(token),
    ])
      .then(([p, s, pr, q]) => {
        setPerf(Array.isArray(p.data) ? p.data : []);
        setSessions(Array.isArray(s.data) ? s.data : []);
        setProgress(Array.isArray(pr.data) ? pr.data : []);
        setQuizPerf(Array.isArray(q.data) ? q.data : []);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load analytics"));
  }, [token]);

  // Summary cards
  const summary = useMemo(() => {
    const uniqueStudents = new Set(progress.map((r) => r.user_id)).size;
    const avgScore = progress.length
      ? progress.reduce((a, r) => a + Number(r.score || 0), 0) / progress.length
      : 0;
    const avgCompletion = progress.length
      ? progress.reduce((a, r) => a + Number(r.completion || 0), 0) / progress.length
      : 0;
    const avgWatchSec = progress.length
      ? Math.round(progress.reduce((a, r) => a + Number(r.time_spent_seconds || 0), 0) / progress.length)
      : 0;
    return { uniqueStudents, avgScore, avgCompletion, avgWatchSec };
  }, [progress]);

  // Per-lesson merged data
  const lessonRows = useMemo(() => {
    const perfMap = new Map(perf.map((r) => [r.lesson_id, r]));
    const quizMap = new Map(quizPerf.map((r) => [r.lesson_id, r]));

    return sessions.map((s) => {
      const p = perfMap.get(s.lesson_id);
      const q = quizMap.get(s.lesson_id);

      // Get all progress rows for this lesson
      const lessonProgress = progress.filter((r) => r.lesson_id === s.lesson_id);
      const studentCount = new Set(lessonProgress.map((r) => r.user_id)).size;
      const avgWatchSec = lessonProgress.length
        ? Math.round(lessonProgress.reduce((a, r) => a + Number(r.time_spent_seconds || 0), 0) / lessonProgress.length)
        : 0;

      // Watch engagement breakdown
      const total = lessonProgress.length || 1;
      const watchedAll = lessonProgress.filter((r) => Number(r.completion) >= 0.85).length;
      const watchedHalf = lessonProgress.filter((r) => {
        const c = Number(r.completion);
        return c >= 0.4 && c < 0.85;
      }).length;
      const pctAll = Math.round((watchedAll / total) * 100);
      const pctHalf = Math.round((watchedHalf / total) * 100);

      return {
        lesson_id: s.lesson_id,
        prompt: s.prompt,
        created_at: s.created_at,
        studentCount,
        avgWatchSec,
        pctAll,
        pctHalf,
        avgScore: p ? Math.round(p.average_score) : null,
        quizCorrectRate: q ? Math.round(q.correct_rate * 100) : null,
        quizAttempts: q ? q.total_attempts : 0,
      };
    });
  }, [sessions, perf, quizPerf, progress]);

  return (
    <PageContainer className="pb-24">
      <Navbar />
      <div className="space-y-6">

        {/* ── Header ── */}
        <section className="rounded-3xl border border-white/15 bg-white/5 p-6">
          <h1 className="mb-1 text-3xl font-bold">Teacher Analytics Hub</h1>
          <p className="text-sm text-slate-400">Real metrics from student sessions — watch time, quiz scores, and engagement.</p>
          {!token && <p className="mt-2 text-sm text-amber-200">Sign in to load class metrics.</p>}
          {error && <p className="mt-2 text-sm text-red-300">{error}</p>}

          <div className="mt-5 grid gap-3 md:grid-cols-4">
            <StatCard label="Students Engaged" value={String(summary.uniqueStudents)} sub="unique learners" />
            <StatCard label="Avg Quiz Score" value={`${Math.round(summary.avgScore)}`} sub="out of 100" />
            <StatCard label="Avg Watch Time" value={fmtTime(summary.avgWatchSec)} sub="per session" />
            <StatCard label="Avg Completion" value={`${Math.round(summary.avgCompletion * 100)}%`} sub="lessons completed" />
          </div>
        </section>

        {/* ── Per-lesson breakdown ── */}
        <section className="rounded-3xl border border-white/15 bg-white/5 p-6">
          <h2 className="mb-4 text-xl font-semibold text-cyan-200">Lesson Engagement Breakdown</h2>

          {lessonRows.length === 0 ? (
            <p className="text-sm text-slate-400">
              {token ? "No lessons yet. Generated lessons will appear here with student engagement data." : "Sign in to view lessons."}
            </p>
          ) : (
            <div className="space-y-3">
              {lessonRows.map((row) => (
                <Link
                  key={row.lesson_id}
                  href={`/lesson?prompt=${encodeURIComponent(row.prompt)}`}
                  className="block rounded-2xl border border-white/10 bg-slate-950/50 p-4 transition-colors hover:border-cyan-400/40 hover:bg-slate-900/60"
                >
                  {/* Title row */}
                  <div className="mb-3 flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-slate-100">{row.prompt}</p>
                      <p className="mt-0.5 text-xs text-slate-500">{fmtDate(row.created_at)} · ID {row.lesson_id.slice(0, 8)}…</p>
                    </div>
                    <span className="shrink-0 rounded-lg bg-slate-800 px-2 py-1 text-xs text-slate-300">
                      {row.studentCount} student{row.studentCount !== 1 ? "s" : ""}
                    </span>
                  </div>

                  {/* Metrics row */}
                  <div className="mb-3 grid grid-cols-3 gap-3 text-center">
                    <div className="rounded-xl bg-white/5 p-2">
                      <p className="text-[10px] uppercase tracking-wider text-slate-500">Avg Watch</p>
                      <p className="mt-0.5 text-sm font-semibold text-cyan-300">{fmtTime(row.avgWatchSec)}</p>
                    </div>
                    <div className="rounded-xl bg-white/5 p-2">
                      <p className="text-[10px] uppercase tracking-wider text-slate-500">Quiz Score</p>
                      <p className={`mt-0.5 text-sm font-semibold ${row.avgScore !== null ? (row.avgScore >= 70 ? "text-emerald-300" : row.avgScore >= 40 ? "text-amber-300" : "text-red-300") : "text-slate-500"}`}>
                        {row.avgScore !== null ? `${row.avgScore}/100` : "—"}
                      </p>
                    </div>
                    <div className="rounded-xl bg-white/5 p-2">
                      <p className="text-[10px] uppercase tracking-wider text-slate-500">Quiz Correct</p>
                      <p className={`mt-0.5 text-sm font-semibold ${row.quizCorrectRate !== null ? (row.quizCorrectRate >= 60 ? "text-emerald-300" : "text-amber-300") : "text-slate-500"}`}>
                        {row.quizCorrectRate !== null ? `${row.quizCorrectRate}%` : "—"}
                        {row.quizAttempts > 0 && <span className="ml-1 text-[10px] text-slate-500">({row.quizAttempts})</span>}
                      </p>
                    </div>
                  </div>

                  {/* Watch engagement bar */}
                  <div>
                    <p className="mb-1 text-[10px] uppercase tracking-wider text-slate-500">Video Engagement</p>
                    <WatchBar pctAll={row.pctAll} pctHalf={row.pctHalf} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </PageContainer>
  );
}
