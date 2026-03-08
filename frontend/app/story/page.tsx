"use client";

import { useState } from "react";

import { StoryScene } from "@/components/content/StoryScene";
import { StreamingRenderer } from "@/components/StreamingRenderer";
import { StreamControlPanel } from "@/components/StreamControlPanel";
import { LearningCanvas } from "@/components/canvas/LearningCanvas";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChoiceButtons } from "@/components/interaction/ChoiceButtons";
import { AudioVisualizer } from "@/components/media/AudioVisualizer";
import { SolarSystemScene } from "@/3d-scenes/SolarSystemScene";

const choices = ["Help your crew", "Search the island", "Decode the starmap", "Build a raft"];

export default function StoryPage() {
  const [lastChoice, setLastChoice] = useState<string>("None yet");

  return (
    <PageContainer className="pb-28" >
      <div data-theme="story">
        <Navbar />
        <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr]">
          <LearningCanvas>
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-4">
                <StoryScene
                  title="Chapter 1: The Singing Horizon"
                  narration="Moonlight glides across the ocean as your crew hears a distant melody. Every choice teaches teamwork."
                />
                <ChoiceButtons choices={choices} onPick={setLastChoice} />
                <p className="text-sm text-orange-100">Last choice: {lastChoice}</p>
                <AudioVisualizer active />
              </div>
              <SolarSystemScene />
            </div>
          </LearningCanvas>

          <Sidebar title="Live AI Stream">
            <div className="space-y-3">
              <StreamControlPanel kind="story" />
              <StreamingRenderer />
            </div>
          </Sidebar>
        </div>
      </div>
    </PageContainer>
  );
}
