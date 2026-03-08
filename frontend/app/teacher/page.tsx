import { EngagementHeatmap } from "@/components/analytics/EngagementHeatmap";
import { LearningStats } from "@/components/analytics/LearningStats";
import { ProgressChart } from "@/components/analytics/ProgressChart";
import { Notification } from "@/components/feedback/Notification";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";

const teacherStats = [
  { label: "Class completion", value: "78%" },
  { label: "Weekly activity", value: "+14%" },
  { label: "Avg score", value: "84" },
  { label: "Needs review", value: "Cell respiration" }
];

export default function TeacherPage() {
  return (
    <PageContainer className="pb-24">
      <Navbar />
      <section className="space-y-5 rounded-3xl border border-white/15 bg-white/5 p-6">
        <h1 className="text-4xl font-bold">Teacher Analytics Hub</h1>
        <LearningStats stats={teacherStats} />
        <div className="grid gap-4 lg:grid-cols-2">
          <ProgressChart />
          <EngagementHeatmap />
        </div>
        <Notification title="Adaptive Path Triggered" detail="17 students auto-assigned a photosynthesis reinforcement quest." />
      </section>
    </PageContainer>
  );
}
