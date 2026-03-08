"use client";

import { useMemo, useState } from "react";

import { SolarSystemScene } from "@/3d-scenes/SolarSystemScene";
import { LearningCanvas } from "@/components/canvas/LearningCanvas";
import { StoryScene } from "@/components/content/StoryScene";
import { ChoiceButtons } from "@/components/interaction/ChoiceButtons";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { AudioVisualizer } from "@/components/media/AudioVisualizer";
import { StreamControlPanel } from "@/components/StreamControlPanel";
import { StreamingRenderer } from "@/components/StreamingRenderer";
import { submitStoryChoice } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useLearningStore } from "@/store/learningStore";

export default function StoryPage() {
  const token = useAuthStore((s) => s.token);
  const stream = useLearningStore((s) => s.stream);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [lastChoice, setLastChoice] = useState<string>("None yet");
  const [error, setError] = useState<string | null>(null);

  const latestNarration = useMemo(() => {
    const item = stream.find((evt) => evt.type === "narration" || evt.type === "text");
    const data = item?.payload?.data as Record<string, unknown> | undefined;
    return String(data?.content ?? "Start a story stream to generate narrative scenes.");
  }, [stream]);

  const dynamicChoices = useMemo(() => {
    const quiz = stream.find((evt) => evt.type === "quiz");
    const data = quiz?.payload?.data as Record<string, unknown> | undefined;
    const options = data?.options;
    return Array.isArray(options) && options.length > 0 ? options.map((value) => String(value)) : [];
  }, [stream]);

  async function pick(choice: string) {
    setLastChoice(choice);
    if (!token || !sessionId) return;
    try {
      setError(null);
      await submitStoryChoice(token, {
        session_id: sessionId,
        scene_id: "scene_live",
        choice_text: choice
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
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-4">
                <StoryScene title="Live AI Story Scene" narration={latestNarration} />
                {dynamicChoices.length > 0 ? (
                  <ChoiceButtons choices={dynamicChoices} onPick={pick} />
                ) : (
                  <p className="text-sm text-slate-300">Choices will appear when AI emits a quiz/interaction event.</p>
                )}
                <p className="text-sm text-orange-100">Last choice: {lastChoice}</p>
                {error && <p className="text-sm text-red-300">{error}</p>}
                <AudioVisualizer active={stream.some((event) => event.type === "audio")} />
              </div>
              <SolarSystemScene />
            </div>
          </LearningCanvas>

          <Sidebar title="Live AI Stream">
            <div className="space-y-3">
              <StreamControlPanel kind="story" onSessionReady={setSessionId} />
              <StreamingRenderer />
            </div>
          </Sidebar>
        </div>
      </div>
    </PageContainer>
  );
}
