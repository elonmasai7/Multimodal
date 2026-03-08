"use client";

import { useMemo, useState } from "react";

import { CellStructureScene } from "@/3d-scenes/CellStructureScene";
import { LearningCanvas } from "@/components/canvas/LearningCanvas";
import { LessonSection } from "@/components/content/LessonSection";
import { Toast } from "@/components/feedback/Toast";
import { DragDropCanvas } from "@/components/interaction/DragDropCanvas";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { StreamControlPanel } from "@/components/StreamControlPanel";
import { StreamingRenderer } from "@/components/StreamingRenderer";
import { SimulationCanvas } from "@/components/visualization/SimulationCanvas";
import { getLessonProgress, submitLessonQuiz } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useLearningStore } from "@/store/learningStore";

export default function LessonPage() {
  const token = useAuthStore((s) => s.token);
  const stream = useLearningStore((s) => s.stream);
  const [lessonId, setLessonId] = useState<string | null>(null);
  const [toast, setToast] = useState("Start a lesson stream to load live generated content");

  const narration = useMemo(() => {
    const item = stream.find((evt) => evt.type === "text" || evt.type === "narration");
    const data = item?.payload?.data as Record<string, unknown> | undefined;
    return String(data?.content ?? "Waiting for AI narration...");
  }, [stream]);

  async function onQuizSubmit(answer: string) {
    if (!token || !lessonId) return;
    const quiz = stream.find((evt) => evt.type === "quiz");
    const data = (quiz?.payload?.data ?? {}) as Record<string, unknown>;
    const questionId = String(data.id ?? "q1");

    try {
      const result = await submitLessonQuiz(token, {
        lesson_id: lessonId,
        question_id: questionId,
        answer,
        time_spent_seconds: 30
      });
      const progress = await getLessonProgress(token, lessonId);
      setToast(
        `Quiz submitted. Correct: ${String(result.data.correct)}. Score: ${Math.round(progress.data.score)}. Completion: ${Math.round(progress.data.completion * 100)}%`
      );
    } catch (err) {
      setToast(err instanceof Error ? err.message : "Quiz submission failed");
    }
  }

  return (
    <PageContainer className="pb-28">
      <div data-theme="lesson">
        <Navbar />
        <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr]">
          <LearningCanvas>
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-4">
                <LessonSection heading="Live AI Lesson" text={narration} />
                <DragDropCanvas />
                <SimulationCanvas />
              </div>
              <div className="space-y-4">
                <CellStructureScene />
                <Toast message={toast} />
              </div>
            </div>
          </LearningCanvas>

          <Sidebar title="Live Lesson Stream">
            <div className="space-y-3">
              <StreamControlPanel kind="lesson" onSessionReady={setLessonId} />
              <StreamingRenderer onQuizSubmit={onQuizSubmit} />
            </div>
          </Sidebar>
        </div>
      </div>
    </PageContainer>
  );
}
