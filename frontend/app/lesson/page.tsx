"use client";

export const dynamic = "force-dynamic";

import { Suspense, useMemo, useState } from "react";

import { CellStructureScene } from "@/3d-scenes/CellStructureScene";
import { Toast } from "@/components/feedback/Toast";
import { QuizPanel } from "@/components/interaction/QuizPanel";
import { SketchPad } from "@/components/interaction/SketchPad";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { NarrationPlayer } from "@/components/media/NarrationPlayer";
import { VideoPlayer } from "@/components/media/VideoPlayer";
import { StreamControlPanel } from "@/components/StreamControlPanel";
import { StreamingRenderer } from "@/components/StreamingRenderer";
import { InterleavedView } from "@/components/content/InterleavedView";
import type { QuizPayload } from "@/types/stream";
import { getLessonProgress, submitLessonQuiz, updateLessonWatchProgress } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useLearningStore } from "@/store/learningStore";

export default function LessonPage() {
  const token = useAuthStore((s) => s.token);
  const stream = useLearningStore((s) => s.stream);
  const [lessonId, setLessonId] = useState<string | null>(null);
  const [toast, setToast] = useState("");

  // Latest video event
  const videoEvent = useMemo(() => {
    const item = stream.slice().reverse().find((evt) => evt.type === "video");
    return item?.payload?.data as Record<string, unknown> | undefined;
  }, [stream]);

  const videoUrl = videoEvent
    ? typeof videoEvent.signed_url === "string"
      ? videoEvent.signed_url
      : typeof videoEvent.url === "string"
      ? videoEvent.url
      : null
    : null;

  const videoClips = Array.isArray(videoEvent?.clips)
    ? (videoEvent!.clips as Record<string, unknown>[])
        .map((c) => (typeof c.signed_url === "string" ? c.signed_url : ""))
        .filter(Boolean)
    : undefined;

  // Latest audio event
  const audioUrl = useMemo(() => {
    const item = stream.slice().reverse().find((evt) => evt.type === "audio");
    const data = item?.payload?.data as Record<string, unknown> | undefined;
    return typeof data?.signed_url === "string" ? data.signed_url : null;
  }, [stream]);

  // Quiz event from stream
  const quizData = useMemo(() => {
    const item = stream.find((evt) => evt.type === "quiz");
    if (!item) return null;
    return item.payload?.data as QuizPayload | undefined;
  }, [stream]);

  // Whether interleaved content has started streaming
  const hasContent = stream.some(
    (evt) => evt.type === "narration" || evt.type === "text" || evt.type === "image"
  );

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
        time_spent_seconds: 30,
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

        {/*
          3-column layout:
          [Left: Interleaved doc + interactive canvases]
          [Center: Video + Audio — the anchor visual experience]
          [Right: Stream controls + status/quiz events]
        */}
        <div className="grid gap-4 lg:grid-cols-[1fr_1.3fr_340px]">

          {/* ── Left: Interleaved narration+diagrams document ── */}
          <div className="space-y-4 overflow-y-auto max-h-[calc(100vh-120px)]">
            {hasContent ? (
              <InterleavedView />
            ) : (
              /* placeholder until stream starts */
              <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-5 text-sm text-slate-400">
                Start a lesson stream — Gemini will weave narration and
                diagrams together here as a single interleaved experience.
              </div>
            )}
            <SketchPad />
          </div>

          {/* ── Center: Video (Veo) + Audio ── */}
          <div className="flex flex-col gap-4">
            <div className="flex-1 min-h-0">
              {videoUrl ? (
                <VideoPlayer
                  src={videoUrl}
                  clips={videoClips}
                  onProgress={(watched, total) => {
                    if (!token || !lessonId || total <= 0) return;
                    updateLessonWatchProgress(token, {
                      lesson_id: lessonId,
                      watched_seconds: watched,
                      video_duration_seconds: total,
                    }).catch(() => {});
                  }}
                />
              ) : (
                <CellStructureScene />
              )}
            </div>

            {audioUrl && (
              <div className="rounded-2xl border border-white/15 bg-slate-950/70 p-3">
                <p className="mb-2 text-xs uppercase tracking-[0.14em] text-cyan-200">
                  Narration Audio
                </p>
                <NarrationPlayer src={audioUrl} />
              </div>
            )}

            {quizData && (
              <QuizPanel
                question={String(quizData.question ?? "Quiz question")}
                options={Array.isArray(quizData.options) ? (quizData.options as string[]) : []}
                onSubmit={onQuizSubmit}
              />
            )}

            {toast && <Toast message={toast} />}
          </div>

          {/* ── Right: Controls + status stream ── */}
          <Sidebar title="Live Lesson Stream">
            <div className="space-y-3">
              <Suspense fallback={null}>
                <StreamControlPanel kind="lesson" onSessionReady={setLessonId} />
              </Suspense>
              {/*
                Exclude narration + image: shown in InterleavedView on the left.
                Exclude video + audio + quiz: shown in the center column.
              */}
              <StreamingRenderer
                exclude={["narration", "image", "video", "audio", "quiz"]}
              />
            </div>
          </Sidebar>

        </div>
      </div>
    </PageContainer>
  );
}
