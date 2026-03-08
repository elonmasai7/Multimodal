"use client";

import { useState } from "react";

import { LearningStats } from "@/components/analytics/LearningStats";
import { ProgressChart } from "@/components/analytics/ProgressChart";
import { EngagementHeatmap } from "@/components/analytics/EngagementHeatmap";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { SearchBar } from "@/components/forms/SearchBar";
import { FileUploader } from "@/components/forms/FileUploader";

const stats = [
  { label: "Lessons completed", value: "42" },
  { label: "Story chapters", value: "19" },
  { label: "Quiz accuracy", value: "88%" },
  { label: "Current streak", value: "12 days" }
];

export default function DashboardPage() {
  const [query, setQuery] = useState("");

  return (
    <PageContainer className="pb-24">
      <Navbar />
      <section className="space-y-4 rounded-3xl border border-white/15 bg-white/5 p-6">
        <h1 className="text-4xl font-bold">Student Mission Control</h1>
        <SearchBar value={query} onChange={setQuery} />
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
