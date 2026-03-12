"use client";

import { useMemo, useState } from "react";

import { StreamingIndicator } from "@/components/feedback/StreamingIndicator";
import { PromptInput } from "@/components/forms/PromptInput";
import { useSSEStream } from "@/hooks/useSSEStream";
import { createSession, lessonStreamUrl, storyStreamUrl } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

type SessionKind = "story" | "lesson";

export function StreamControlPanel({ kind, onSessionReady }: { kind: SessionKind; onSessionReady?: (id: string) => void }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [prompt, setPrompt] = useState(
    kind === "story" ? "A moonlit pirate adventure about teamwork" : "Explain photosynthesis with diagrams"
  );
  const [error, setError] = useState<string | null>(null);
  const token = useAuthStore((s) => s.token);
  const { connect, disconnect, connected } = useSSEStream();

  const streamUrl = useMemo(() => {
    if (!sessionId || !token) return null;
    return kind === "story" ? storyStreamUrl(sessionId, prompt, token) : lessonStreamUrl(sessionId, prompt, token);
  }, [kind, prompt, sessionId, token]);

  async function start() {
    setError(null);
    if (!token) {
      setError("Sign in first to start AI generation.");
      return;
    }
    try {
      const created = await createSession(prompt, kind, token);
      const id = kind === "story" ? created.data.session_id : created.data.lesson_id;
      setSessionId(id);
      onSessionReady?.(id);
      const url = kind === "story" ? storyStreamUrl(id, prompt, token) : lessonStreamUrl(id, prompt, token);
      connect(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    }
  }

  return (
    <div className="space-y-3 rounded-2xl border border-white/15 bg-white/5 p-4">
      <div className="flex items-center justify-between gap-3">
        <StreamingIndicator active={connected} />
        <div className="text-xs text-slate-300">{sessionId ? `Session: ${sessionId.slice(0, 8)}` : "No session"}</div>
      </div>
      <PromptInput value={prompt} onChange={setPrompt} />
      {error && <p className="text-xs text-red-300">{error}</p>}
      <div className="flex gap-2">
        <button onClick={start} className="rounded-xl bg-cyan-400 px-3 py-2 text-sm font-semibold text-slate-950">
          Start Live Stream
        </button>
        <button onClick={disconnect} className="rounded-xl border border-white/25 px-3 py-2 text-sm text-slate-200">
          Stop
        </button>
      </div>
    </div>
  );
}
