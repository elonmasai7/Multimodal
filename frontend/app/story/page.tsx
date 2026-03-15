"use client";

export const dynamic = "force-dynamic";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";

import { SolarSystemScene } from "@/3d-scenes/SolarSystemScene";
import { LearningCanvas } from "@/components/canvas/LearningCanvas";
import { StoryBook } from "@/components/content/StoryBook";
import { StoryQuiz } from "@/components/content/StoryQuiz";
import { SharePanel } from "@/components/content/SharePanel";
import { StoryScene } from "@/components/content/StoryScene";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { AudioVisualizer } from "@/components/media/AudioVisualizer";
import { VideoPlayer } from "@/components/media/VideoPlayer";
import { StreamControlPanel } from "@/components/StreamControlPanel";
import { StreamingRenderer } from "@/components/StreamingRenderer";
import { saveStoryPages, submitStoryChoice } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useLearningStore } from "@/store/learningStore";

export default function StoryPage() {
  const token = useAuthStore((s) => s.token);
  const stream = useLearningStore((s) => s.stream);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const savedForSession = useRef<string | null>(null);

  // Auto-save book pages to Firestore once the stream is complete
  useEffect(() => {
    const isDone = stream.some((evt) => evt.type === "done");
    if (!isDone || !sessionId || !token || savedForSession.current === sessionId) return;
    savedForSession.current = sessionId;

    // stream is newest-first — reverse for chronological order
    const pages = [...stream]
      .reverse()
      .filter((evt) => evt.type === "narration" || evt.type === "image")
      .map((evt) => {
        const data = evt.payload?.data as Record<string, unknown> | undefined;
        if (evt.type === "narration") {
          return { type: "narration" as const, content: String(data?.content ?? "") };
        }
        return {
          type: "image" as const,
          gcs_uri: typeof data?.gcs_uri === "string" ? data.gcs_uri : undefined,
          caption: typeof data?.caption === "string" ? data.caption : undefined,
        };
      })
      .filter((p) => (p.type === "narration" ? p.content : p.gcs_uri));

    if (pages.length > 0) {
      saveStoryPages(token, sessionId, pages).catch(() => {});
    }
  }, [stream, sessionId, token]);

  const latestNarration = useMemo(() => {
    const item = stream.find((evt) => evt.type === "narration" || evt.type === "text");
    const data = item?.payload?.data as Record<string, unknown> | undefined;
    return String(data?.content ?? "Start a story stream to generate narrative scenes.");
  }, [stream]);

  const latestVideoUrl = useMemo(() => {
    const item = stream.find((evt) => evt.type === "video");
    const data = item?.payload?.data as Record<string, unknown> | undefined;
    return typeof data?.signed_url === "string" ? data.signed_url : typeof data?.url === "string" ? data.url : null;
  }, [stream]);

  async function handleQuizChoice(choice: string) {
    if (!token || !sessionId) return;
    try {
      setError(null);
      await submitStoryChoice(token, {
        session_id: sessionId,
        scene_id: "scene_live",
        choice_text: choice,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit choice");
    }
  }

  return (
    <PageContainer className="pb-28">
      <div data-theme="story">
        <Navbar />
        <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr]">
          <LearningCanvas>
            <div className="space-y-4">
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="space-y-4">
                  <StoryScene title="Live AI Story Scene" narration={latestNarration} />
                  <AudioVisualizer active={stream.some((event) => event.type === "audio")} />
                  {error && <p className="text-sm text-red-300">{error}</p>}
                </div>
                {latestVideoUrl ? (
                  <div className="flex items-center justify-center rounded-2xl border border-white/15 bg-slate-950/70 p-4">
                    <VideoPlayer src={latestVideoUrl} />
                  </div>
                ) : (
                  <SolarSystemScene />
                )}
              </div>
              <StoryBook />
              <StoryQuiz onChoice={handleQuizChoice} />
              {stream.some((evt) => evt.type === "done") && sessionId && (
                <SharePanel
                  storyUrl={`${typeof window !== "undefined" ? window.location.origin : ""}/story/${sessionId}`}
                  title="My Msomi Story"
                  videoUrl={latestVideoUrl}
                />
              )}
            </div>
          </LearningCanvas>

          <Sidebar title="Live AI Stream">
            <div className="space-y-3">
              <Suspense fallback={null}>
                <StreamControlPanel kind="story" onSessionReady={setSessionId} />
              </Suspense>
              <StreamingRenderer exclude={["video", "quiz", "image", "narration"]} />
            </div>
          </Sidebar>
        </div>
      </div>
    </PageContainer>
  );
}
