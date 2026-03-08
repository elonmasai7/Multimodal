"use client";

import { AnimatePresence, motion } from "framer-motion";

import { AIImageRenderer } from "@/components/media/AIImageRenderer";
import { NarrationPlayer } from "@/components/media/NarrationPlayer";
import { QuizPanel } from "@/components/interaction/QuizPanel";
import { useLearningStore } from "@/store/learningStore";
import type { QuizPayload } from "@/types/stream";

function toData(payload: unknown): Record<string, unknown> {
  if (!payload || typeof payload !== "object") return {};
  return payload as Record<string, unknown>;
}

export function StreamingRenderer({ onQuizSubmit }: { onQuizSubmit?: (answer: string) => void }) {
  const stream = useLearningStore((s) => s.stream);

  return (
    <div className="space-y-3" aria-live="polite">
      <AnimatePresence initial={false}>
        {stream.map((item) => {
          const data = toData(item.payload?.data);
          const imageUrl = typeof data.signed_url === "string" ? data.signed_url : typeof data.url === "string" ? data.url : null;
          const audioUrl = typeof data.signed_url === "string" ? data.signed_url : typeof data.url === "string" ? data.url : null;

          return (
            <motion.article
              key={item.id}
              initial={{ opacity: 0, y: 14, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.3 }}
              className="rounded-2xl border border-white/15 bg-slate-950/70 p-3"
            >
              <p className="mb-2 text-xs uppercase tracking-[0.14em] text-cyan-200">{item.type}</p>

              {(item.type === "text" || item.type === "narration" || item.type === "status" || item.type === "error") && (
                <p className="text-sm text-slate-100">{String(data.content ?? data.message ?? data.raw ?? "")}</p>
              )}

              {item.type === "image" && imageUrl && <AIImageRenderer src={imageUrl} alt="AI generated visual" />}

              {item.type === "audio" && audioUrl && <NarrationPlayer src={audioUrl} />}

              {item.type === "quiz" && (
                <QuizPanel
                  question={String((data as QuizPayload).question ?? "Quiz question")}
                  options={Array.isArray((data as QuizPayload).options) ? ((data as QuizPayload).options as string[]) : []}
                  onSubmit={(answer) => onQuizSubmit?.(answer)}
                />
              )}
            </motion.article>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
