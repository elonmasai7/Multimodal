"use client";

import { useMemo, useState } from "react";

import { StreamingIndicator } from "@/components/feedback/StreamingIndicator";
import { PromptInput } from "@/components/forms/PromptInput";
import { useSSEStream } from "@/hooks/useSSEStream";

type SessionKind = "story" | "lesson";

export function StreamControlPanel({ kind }: { kind: SessionKind }) {
  const [sessionId, setSessionId] = useState("demo");
  const [prompt, setPrompt] = useState(kind === "story" ? "A moonlit pirate adventure about teamwork" : "Explain photosynthesis with diagrams");
  const { connect, disconnect, connected } = useSSEStream();

  const streamUrl = useMemo(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";
    const route = kind === "story" ? `story/stream/${sessionId}` : `lesson/stream/${sessionId}`;
    return `${base}/${route}?prompt=${encodeURIComponent(prompt)}`;
  }, [kind, prompt, sessionId]);

  return (
    <div className="space-y-3 rounded-2xl border border-white/15 bg-white/5 p-4">
      <div className="flex items-center justify-between gap-3">
        <StreamingIndicator active={connected} />
        <input
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          className="w-32 rounded-lg border border-white/20 bg-slate-950/60 px-2 py-1 text-xs text-white"
          aria-label="Session id"
        />
      </div>
      <PromptInput value={prompt} onChange={setPrompt} />
      <div className="flex gap-2">
        <button onClick={() => connect(streamUrl)} className="rounded-xl bg-cyan-400 px-3 py-2 text-sm font-semibold text-slate-950">
          Start Live Stream
        </button>
        <button onClick={disconnect} className="rounded-xl border border-white/25 px-3 py-2 text-sm text-slate-200">
          Stop
        </button>
      </div>
    </div>
  );
}
