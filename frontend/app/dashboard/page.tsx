"use client";

import { useEffect, useMemo, useState } from "react";

import { EngagementHeatmap } from "@/components/analytics/EngagementHeatmap";
import { LearningStats } from "@/components/analytics/LearningStats";
import { ProgressChart } from "@/components/analytics/ProgressChart";
import { FileUploader } from "@/components/forms/FileUploader";
import { SearchBar } from "@/components/forms/SearchBar";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { getStudentProgressAnalytics } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export default function DashboardPage() {
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const token = useAuthStore((s) => s.token);
  const userId = useAuthStore((s) => s.userId);

  useEffect(() => {
    async function load() {
      if (!token) return;
      try {
        setError(null);
        const response = await getStudentProgressAnalytics(token, userId ?? undefined);
        setRows(Array.isArray(response.data) ? response.data : []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      }
    }
    load();
  }, [token, userId]);

  const stats = useMemo(() => {
    if (rows.length === 0) {
      return [
        { label: "Lessons completed", value: "0" },
        { label: "Story chapters", value: "0" },
        { label: "Quiz accuracy", value: "0%" },
        { label: "Current streak", value: "0 days" }
      ];
    }

    const avgScore = rows.reduce((acc, row) => acc + Number(row.score || 0), 0) / rows.length;
    const avgCompletion = rows.reduce((acc, row) => acc + Number(row.completion || 0), 0) / rows.length;
    return [
      { label: "Lessons completed", value: String(rows.length) },
      { label: "Story chapters", value: "Live" },
      { label: "Quiz accuracy", value: `${Math.round(avgScore)}%` },
      { label: "Avg completion", value: `${Math.round(avgCompletion * 100)}%` }
    ];
  }, [rows]);

  return (
    <PageContainer className="pb-24">
      <Navbar />
      <section className="space-y-4 rounded-3xl border border-white/15 bg-white/5 p-6">
        <h1 className="text-4xl font-bold">Student Mission Control</h1>
        <SearchBar value={query} onChange={setQuery} />
        {error && <p className="text-sm text-red-300">{error}</p>}
        {!token && <p className="text-sm text-amber-200">Sign in to load real analytics.</p>}
        <LearningStats stats={stats} />
        <div className="grid gap-4 lg:grid-cols-2">
          <ProgressChart />
          <EngagementHeatmap />
        </div>
        <FileUploader />
      </section>
    </PageContainer>
  );
}
