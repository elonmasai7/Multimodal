"use client";

import { useEffect, useMemo, useState } from "react";

import { EngagementHeatmap } from "@/components/analytics/EngagementHeatmap";
import { LearningStats } from "@/components/analytics/LearningStats";
import { ProgressChart } from "@/components/analytics/ProgressChart";
import { FileUploader } from "@/components/forms/FileUploader";
import { SearchBar } from "@/components/forms/SearchBar";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { getLessonSessions, getStorySessions, getStudentProgressAnalytics } from "@/lib/api";
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
      {rounded}%
    </span>
  );
}

function CompletionBar({ value }: { value: number }) {
  const pct = Math.round(Math.min(1, value) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-cyan-400"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-slate-400">{pct}%</span>
    </div>
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
  if (seconds < 60) return `${seconds}s`;
  return `${Math.round(seconds / 60)}m`;
}

export default function DashboardPage() {
  const [query, setQuery] = useState("");
  const [progressRows, setProgressRows] = useState<ProgressRow[]>([]);
  const [lessonSessions, setLessonSessions] = useState<LessonSession[]>([]);
  const [storySessions, setStorySessions] = useState<StorySession[]>([]);
  const [error, setError] = useState<string | null>(null);
  const token = useAuthStore((s) => s.token);
  const userId = useAuthStore((s) => s.userId);

  useEffect(() => {
    async function load() {
      if (!token) return;
      try {
        setError(null);
        const [progRes, lessonRes, storyRes] = await Promise.all([
          getStudentProgressAnalytics(token, userId ?? undefined),
          getLessonSessions(token),
          getStorySessions(token),
        ]);
        setProgressRows(Array.isArray(progRes.data) ? progRes.data : []);
        setLessonSessions(Array.isArray(lessonRes.data) ? lessonRes.data : []);
        setStorySessions(Array.isArray(storyRes.data) ? storyRes.data : []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      }
    }
    load();
  }, [token, userId]);

  // Map progress by lesson_id for quick lookup
  const progressMap = useMemo(() => {
    const map: Record<string, ProgressRow> = {};
    for (const row of progressRows) map[row.lesson_id] = row;
    return map;
  }, [progressRows]);

  const stats = useMemo(() => {
    if (progressRows.length === 0) {
      return [
        { label: "Lessons completed", value: "0" },
        { label: "Stories explored", value: String(storySessions.length) },
        { label: "Quiz accuracy", value: "0%" },
        { label: "Time studying", value: "0m" },
      ];
    }
    const avgScore = progressRows.reduce((a, r) => a + Number(r.score || 0), 0) / progressRows.length;
    const totalTime = progressRows.reduce((a, r) => a + Number(r.time_spent_seconds || 0), 0);
    return [
      { label: "Lessons completed", value: String(progressRows.length) },
      { label: "Stories explored", value: String(storySessions.length) },
      { label: "Quiz accuracy", value: `${Math.round(avgScore)}%` },
      { label: "Time studying", value: formatTime(totalTime) },
    ];
  }, [progressRows, storySessions.length]);

  // Filter lessons by search query
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
            <ProgressChart />
            <EngagementHeatmap />
          </div>
          <FileUploader />
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
                return (
                  <div
                    key={s.lesson_id}
                    className="rounded-2xl border border-white/10 bg-slate-950/50 p-4"
                  >
                    {/* Topic */}
                    <p className="mb-2 text-sm font-medium leading-snug text-slate-100">{s.prompt}</p>

                    {/* Metrics row */}
                    <div className="flex flex-wrap items-center gap-3">
                      {prog ? (
                        <>
                          <ScoreBadge score={prog.score} />
                          <CompletionBar value={prog.completion} />
                          {prog.time_spent_seconds > 0 && (
                            <span className="text-xs text-slate-400">
                              {formatTime(prog.time_spent_seconds)} spent
                            </span>
                          )}
                        </>
                      ) : (
                        <span className="text-xs text-slate-500">No score recorded yet</span>
                      )}
                      {s.quiz_attempts > 0 && (
                        <span className="text-xs text-slate-400">
                          {s.quiz_attempts} quiz attempt{s.quiz_attempts !== 1 ? "s" : ""}
                        </span>
                      )}
                    </div>

                    {/* Date */}
                    <p className="mt-2 text-xs text-slate-600">{formatDate(s.created_at)}</p>
                  </div>
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
              {filteredStories.map((s) => {
                const sceneNum = parseInt(s.current_scene.replace(/\D/g, "") || "1", 10);
                return (
                  <div
                    key={s.session_id}
                    className="rounded-2xl border border-white/10 bg-slate-950/50 p-4"
                  >
                    {/* Story premise */}
                    <p className="mb-2 text-sm font-medium leading-snug text-slate-100">{s.prompt}</p>

                    {/* Progress row */}
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <span className="text-violet-400">Scene {sceneNum}</span>
                        {s.choices_made > 0 && (
                          <span>&middot; {s.choices_made} choice{s.choices_made !== 1 ? "s" : ""} made</span>
                        )}
                      </span>
                    </div>

                    {/* Date */}
                    <p className="mt-2 text-xs text-slate-600">{formatDate(s.created_at)}</p>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </PageContainer>
  );
}
