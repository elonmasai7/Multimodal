"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { EngagementHeatmap } from "@/components/analytics/EngagementHeatmap";
import { LearningStats } from "@/components/analytics/LearningStats";
import { ProgressChart } from "@/components/analytics/ProgressChart";
import { SearchBar } from "@/components/forms/SearchBar";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import {
  getLessonSessions,
  getMyQuizPerformanceAnalytics,
  getStorySessions,
  getStudentProgressAnalytics,
} from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

type LessonSession = {
  lesson_id: string;
  prompt: string;
  quiz_attempts: number;
  created_at: string;
};

type StorySession = {
  session_id: string;
  prompt: string;
  choices_made: number;
  current_scene: string;
  created_at: string;
};

type ProgressRow = {
  lesson_id: string;
  score: number;
  completion: number;
  time_spent_seconds: number;
  updated_at?: string;
};

type QuizPerfRow = {
  lesson_id: string;
  total_attempts: number;
  correct_count: number;
  correct_rate: number;
};

function ScoreBadge({ score }: { score: number }) {
  const rounded = Math.round(score);
  const color =
    rounded >= 80
      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
      : rounded >= 50
      ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
      : "bg-red-500/20 text-red-300 border-red-500/30";
  return (
    <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${color}`}>
      {rounded}/100
    </span>
  );
}

function CompletionBar({ value }: { value: number }) {
  const pct = Math.round(Math.min(1, value) * 100);
  const color = pct >= 85 ? "bg-emerald-400" : pct >= 40 ? "bg-amber-400" : "bg-red-400/70";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-white/10">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400">{pct}%</span>
    </div>
  );
}

function QuizRateBadge({ correct, total }: { correct: number; total: number }) {
  if (total === 0) return null;
  const pct = Math.round((correct / total) * 100);
  const color = pct >= 60 ? "text-emerald-300" : "text-amber-300";
  return (
    <span className={`text-xs font-medium ${color}`}>
      {correct}/{total} correct ({pct}%)
    </span>
  );
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

function formatTime(seconds: number) {
  if (seconds <= 0) return "0s";
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s > 0 ? `${m}m ${s}s` : `${m}m`;
}

export default function DashboardPage() {
  const [query, setQuery] = useState("");
  const [progressRows, setProgressRows] = useState<ProgressRow[]>([]);
  const [lessonSessions, setLessonSessions] = useState<LessonSession[]>([]);
  const [storySessions, setStorySessions] = useState<StorySession[]>([]);
  const [myQuizPerf, setMyQuizPerf] = useState<QuizPerfRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const token = useAuthStore((s) => s.token);
  const userId = useAuthStore((s) => s.userId);

  useEffect(() => {
    if (!token) return;
    setError(null);
    Promise.all([
      getStudentProgressAnalytics(token, userId ?? undefined),
      getLessonSessions(token),
      getStorySessions(token),
      getMyQuizPerformanceAnalytics(token),
    ])
      .then(([progRes, lessonRes, storyRes, quizRes]) => {
        setProgressRows(Array.isArray(progRes.data) ? progRes.data : []);
        setLessonSessions(Array.isArray(lessonRes.data) ? lessonRes.data : []);
        setStorySessions(Array.isArray(storyRes.data) ? storyRes.data : []);
        setMyQuizPerf(Array.isArray(quizRes.data) ? quizRes.data : []);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load data"));
  }, [token, userId]);

  const progressMap = useMemo(() => {
    const map: Record<string, ProgressRow> = {};
    for (const row of progressRows) map[row.lesson_id] = row;
    return map;
  }, [progressRows]);

  const quizMap = useMemo(() => {
    const map: Record<string, QuizPerfRow> = {};
    for (const row of myQuizPerf) map[row.lesson_id] = row;
    return map;
  }, [myQuizPerf]);

  const stats = useMemo(() => {
    const avgScore = progressRows.length
      ? Math.round(progressRows.reduce((a: number, r: ProgressRow) => a + Number(r.score || 0), 0) / progressRows.length)
      : 0;
    const totalTimeSec = progressRows.reduce((a: number, r: ProgressRow) => a + Number(r.time_spent_seconds || 0), 0);
    const totalCorrect = myQuizPerf.reduce((a: number, r: QuizPerfRow) => a + r.correct_count, 0);
    const totalAttempts = myQuizPerf.reduce((a: number, r: QuizPerfRow) => a + r.total_attempts, 0);
    const quizAccuracy = totalAttempts > 0 ? `${Math.round((totalCorrect / totalAttempts) * 100)}%` : "—";
    return [
      { label: "Lessons started", value: String(lessonSessions.length) },
      { label: "Avg quiz score", value: progressRows.length ? `${avgScore}/100` : "—" },
      { label: "Quiz accuracy", value: quizAccuracy },
      { label: "Total watch time", value: formatTime(totalTimeSec) },
    ];
  }, [progressRows, lessonSessions.length, myQuizPerf]);

  // Scores sorted by updated_at for ProgressChart
  const { chartScores, chartLabels } = useMemo(() => {
    const sorted = [...progressRows].sort((a, b) =>
      (a.updated_at ?? "").localeCompare(b.updated_at ?? "")
    );
    return {
      chartScores: sorted.map((r: ProgressRow) => Math.round(r.score)),
      chartLabels: sorted.map((r: ProgressRow) => {
        const s = lessonSessions.find((l: LessonSession) => l.lesson_id === r.lesson_id);
        return s ? s.prompt.split(" ").slice(0, 3).join(" ") : r.lesson_id.slice(0, 6);
      }),
    };
  }, [progressRows, lessonSessions]);

  // Completions for EngagementHeatmap — aligned to lesson session order
  const { heatmapCompletions, heatmapLabels } = useMemo(() => {
    return {
      heatmapCompletions: lessonSessions.map((s: LessonSession) => {
        const p = progressMap[s.lesson_id];
        return p ? Number(p.completion) : 0;
      }),
      heatmapLabels: lessonSessions.map((s: LessonSession) => s.prompt.split(" ").slice(0, 3).join(" ")),
    };
  }, [lessonSessions, progressMap]);

  const filteredLessons = lessonSessions.filter(
    (s) => !query || s.prompt.toLowerCase().includes(query.toLowerCase())
  );
  const filteredStories = storySessions.filter(
    (s) => !query || s.prompt.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <PageContainer className="pb-24">
      <Navbar />
      <div className="space-y-6">

        {/* ── Overview ── */}
        <section className="space-y-4 rounded-3xl border border-white/15 bg-white/5 p-6">
          <h1 className="text-4xl font-bold">Student Mission Control</h1>
          {!token && <p className="text-sm text-amber-200">Sign in to load your learning history.</p>}
          {error && <p className="text-sm text-red-300">{error}</p>}
          <LearningStats stats={stats} />
          <div className="grid gap-4 lg:grid-cols-2">
            <ProgressChart values={chartScores} labels={chartLabels} />
            <EngagementHeatmap completions={heatmapCompletions} labels={heatmapLabels} />
          </div>
        </section>

        {/* ── Search ── */}
        {token && (lessonSessions.length > 0 || storySessions.length > 0) && (
          <SearchBar value={query} onChange={setQuery} />
        )}

        {/* ── Lesson Archives ── */}
        <section className="rounded-3xl border border-white/15 bg-white/5 p-6">
          <div className="mb-4 flex items-center gap-3">
            <h2 className="text-xl font-semibold text-cyan-200">My Lessons</h2>
            {filteredLessons.length > 0 && (
              <span className="rounded-full bg-cyan-500/15 px-2 py-0.5 text-xs text-cyan-300">
                {filteredLessons.length}
              </span>
            )}
          </div>
          {!token ? (
            <p className="text-sm text-slate-400">Sign in to see your lesson history.</p>
          ) : filteredLessons.length === 0 ? (
            <p className="text-sm text-slate-400">
              {query ? "No lessons match your search." : "No lessons yet — start one from the Lesson page."}
            </p>
          ) : (
            <div className="space-y-3">
              {filteredLessons.map((s) => {
                const prog = progressMap[s.lesson_id];
                const quiz = quizMap[s.lesson_id];
                return (
                  <Link
                    key={s.lesson_id}
                    href={`/lesson?prompt=${encodeURIComponent(s.prompt)}`}
                    className="block rounded-2xl border border-white/10 bg-slate-950/50 p-4 transition-colors hover:border-cyan-400/40 hover:bg-slate-900/60"
                  >
                    <p className="mb-2 text-sm font-medium leading-snug text-slate-100">{s.prompt}</p>

                    {/* Metrics grid */}
                    <div className="mb-2 grid grid-cols-3 gap-2 text-center">
                      <div className="rounded-xl bg-white/5 p-2">
                        <p className="text-[10px] uppercase tracking-wider text-slate-500">Quiz Score</p>
                        {prog ? (
                          <ScoreBadge score={prog.score} />
                        ) : (
                          <span className="text-xs text-slate-500">—</span>
                        )}
                      </div>
                      <div className="rounded-xl bg-white/5 p-2">
                        <p className="text-[10px] uppercase tracking-wider text-slate-500">Watch Time</p>
                        <p className="mt-0.5 text-sm font-semibold text-cyan-300">
                          {prog && prog.time_spent_seconds > 0 ? formatTime(prog.time_spent_seconds) : "—"}
                        </p>
                      </div>
                      <div className="rounded-xl bg-white/5 p-2">
                        <p className="text-[10px] uppercase tracking-wider text-slate-500">Quiz Correct</p>
                        <p className="mt-0.5 text-xs font-medium">
                          {quiz ? (
                            <QuizRateBadge correct={quiz.correct_count} total={quiz.total_attempts} />
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </p>
                      </div>
                    </div>

                    {/* Video completion bar */}
                    {prog && (
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] uppercase tracking-wider text-slate-500">Video</span>
                        <CompletionBar value={prog.completion} />
                      </div>
                    )}

                    <p className="mt-2 text-xs text-slate-600">{formatDate(s.created_at)}</p>
                  </Link>
                );
              })}
            </div>
          )}
        </section>

        {/* ── Story Archives ── */}
        <section className="rounded-3xl border border-white/15 bg-white/5 p-6">
          <div className="mb-4 flex items-center gap-3">
            <h2 className="text-xl font-semibold text-violet-300">My Stories</h2>
            {filteredStories.length > 0 && (
              <span className="rounded-full bg-violet-500/15 px-2 py-0.5 text-xs text-violet-300">
                {filteredStories.length}
              </span>
            )}
          </div>
          {!token ? (
            <p className="text-sm text-slate-400">Sign in to see your story adventures.</p>
          ) : filteredStories.length === 0 ? (
            <p className="text-sm text-slate-400">
              {query ? "No stories match your search." : "No stories yet — start one from the Story page."}
            </p>
          ) : (
            <div className="space-y-3">
              {filteredStories.map((s: StorySession) => {
                const sceneNum = parseInt(s.current_scene.replace(/\D/g, "") || "1", 10);
                return (
                  <Link
                    key={s.session_id}
                    href={`/story/${s.session_id}`}
                    className="block rounded-2xl border border-white/10 bg-slate-950/50 p-4 transition-colors hover:border-violet-400/40 hover:bg-slate-900/60"
                  >
                    <p className="mb-2 text-sm font-medium leading-snug text-slate-100">{s.prompt}</p>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                      <span className="text-violet-400">Scene {sceneNum}</span>
                      {s.choices_made > 0 && (
                        <span>{s.choices_made} choice{s.choices_made !== 1 ? "s" : ""} made</span>
                      )}
                      <span className="text-violet-500/60">Read book →</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-600">{formatDate(s.created_at)}</p>
                  </Link>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </PageContainer>
  );
}
