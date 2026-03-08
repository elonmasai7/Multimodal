"use client";

import { useLearningStore } from "@/store/learningStore";

export function NarrationPlayer({ src }: { src: string }) {
  const audioEnabled = useLearningStore((s) => s.audioEnabled);
  if (!audioEnabled) return <p className="text-xs text-slate-400">Audio is disabled.</p>;
  return <audio controls src={src} className="w-full" preload="metadata" />;
}
