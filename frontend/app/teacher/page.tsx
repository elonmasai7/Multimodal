"use client";

import { useEffect, useMemo, useState } from "react";

import { EngagementHeatmap } from "@/components/analytics/EngagementHeatmap";
import { LearningStats } from "@/components/analytics/LearningStats";
import { ProgressChart } from "@/components/analytics/ProgressChart";
import { Notification } from "@/components/feedback/Notification";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { getLessonPerformanceAnalytics, getLessonSessions } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

type LessonSession = {
  lesson_id: string;
  prompt: string;
  duration: number | null;
  quiz_attempts: number;
  created_at: string;
};

export default function TeacherPage() {
  const token = useAuthStore((s) => s.token);
  const [rows, setRows] = useState<any[]>([]);
  const [sessions, setSessions] = useState<LessonSession[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      if (!token) return;
      try {
        setError(null);
        const [perfRes, sessRes] = await Promise.all([
          getLessonPerformanceAnalytics(token),
          getLessonSessions(token),
        ]);
        setRows(Array.isArray(perfRes.data) ? perfRes.data : []);
        setSessions(Array.isArray(sessRes.data) ? sessRes.data : []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load lesson data");
      }
    }
    load();
  }, [token]);

  const teacherStats = useMemo(() => {
    if (rows.length === 0) {
      return [
        { label: "Class completion", value: "0%" },
        { label: "Weekly activity", value: "0" },
        { label: "Avg score", value: "0" },
        { label: "Top lesson", value: "N/A" }
      ];
    }
    const avgCompletion = rows.reduce((a, r) => a + Number(r.completion_rate || 0), 0) / rows.length;
    const avgScore = rows.reduce((a, r) => a + Number(r.average_score || 0), 0) / rows.length;
    const top = rows[0];
    return [
      { label: "Class completion", value: `${Math.round(avgCompletion * 100)}%` },
      { label: "Weekly activity", value: String(rows.length) },
      { label: "Avg score", value: String(Math.round(avgScore)) },
      { label: "Top lesson", value: String(top.lesson_id) }
    ];
  }, [rows]);

  return (
    <PageContainer className="pb-24">
      <Navbar />
      <div className="space-y-6">
        <section className="space-y-5 rounded-3xl border border-white/15 bg-white/5 p-6">
          <h1 className="text-4xl font-bold">Teacher Analytics Hub</h1>
          {!token && <p className="text-sm text-amber-200">Sign in to load real class metrics.</p>}
          {error && <p className="text-sm text-red-300">{error}</p>}
          <LearningStats stats={teacherStats} />
          <div className="grid gap-4 lg:grid-cols-2">
            <ProgressChart />
            <EngagementHeatmap />
          </div>
          <Notification
            title="Live Analytics"
            detail="Teacher metrics are now sourced from Cloud SQL progress records and quiz attempts."
          />
        </section>

        {/* ── Lesson Archives ── */}
        <section className="rounded-3xl border border-white/15 bg-white/5 p-6">
          <h2 className="mb-4 text-2xl font-semibold text-cyan-200">Lesson Archives</h2>
          {sessions.length === 0 ? (
            <p className="text-sm text-slate-400">
              {token ? "No lessons generated yet. Start a lesson stream to see it archived here." : "Sign in to view archived lessons."}
            </p>
          ) : (
            <div className="space-y-3">
              {sessions.map((s) => {
                const date = s.created_at
                  ? new Date(s.created_at).toLocaleString(undefined, {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })
                  : "—";
                return (
                  <div
                    key={s.lesson_id}
                    className="flex items-start justify-between gap-4 rounded-2xl border border-white/10 bg-slate-950/50 px-4 py-3"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-slate-100">{s.prompt}</p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        ID: {s.lesson_id.slice(0, 8)}&hellip; &middot; {date}
                      </p>
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1 text-xs text-slate-400">
                      {s.duration != null && <span>{s.duration}s video</span>}
                      <span>{s.quiz_attempts} quiz attempt{s.quiz_attempts !== 1 ? "s" : ""}</span>
                    </div>
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
