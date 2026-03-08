"use client";

import { useEffect, useMemo, useState } from "react";

import { EngagementHeatmap } from "@/components/analytics/EngagementHeatmap";
import { LearningStats } from "@/components/analytics/LearningStats";
import { ProgressChart } from "@/components/analytics/ProgressChart";
import { Notification } from "@/components/feedback/Notification";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { getLessonPerformanceAnalytics } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export default function TeacherPage() {
  const token = useAuthStore((s) => s.token);
  const [rows, setRows] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      if (!token) return;
      try {
        setError(null);
        const response = await getLessonPerformanceAnalytics(token);
        setRows(Array.isArray(response.data) ? response.data : []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load lesson performance");
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
    </PageContainer>
  );
}
