"use client";

import { create } from "zustand";

import type { LearningMode } from "@/design-system";
import type { StreamItem } from "@/types/stream";

type LearningState = {
  mode: LearningMode;
  reducedMotion: boolean;
  audioEnabled: boolean;
  stream: StreamItem[];
  setMode: (mode: LearningMode) => void;
  setReducedMotion: (value: boolean) => void;
  setAudioEnabled: (value: boolean) => void;
  pushEvent: (item: StreamItem) => void;
  clearStream: () => void;
};

export const useLearningStore = create<LearningState>((set) => ({
  mode: "story",
  reducedMotion: false,
  audioEnabled: true,
  stream: [],
  setMode: (mode) => set({ mode }),
  setReducedMotion: (reducedMotion) => set({ reducedMotion }),
  setAudioEnabled: (audioEnabled) => set({ audioEnabled }),
  pushEvent: (item) => set((state) => ({ stream: [item, ...state.stream].slice(0, 120) })),
  clearStream: () => set({ stream: [] })
}));
