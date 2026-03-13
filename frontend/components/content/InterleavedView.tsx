"use client";

import { AnimatePresence, motion } from "framer-motion";
import Image from "next/image";

import { useLearningStore } from "@/store/learningStore";

function toData(payload: unknown): Record<string, unknown> {
  if (!payload || typeof payload !== "object") return {};
  return payload as Record<string, unknown>;
}

/**
 * Renders the interleaved Gemini output as a flowing document:
 * text paragraphs and inline diagrams appear in the order they were
 * streamed, creating the "creative director" mixed-media experience.
 */
export function InterleavedView() {
  const stream = useLearningStore((s) => s.stream);

  // Collect narration + image events in stream order — these are the
  // interleaved parts produced by the single Gemini call.
  const parts = stream.filter(
    (item) => item.type === "narration" || item.type === "image"
  );

  const titleItem = stream.find((item) => item.type === "text");
  const title = titleItem
    ? String(toData(titleItem.payload?.data).title ?? "")
    : "";

  if (parts.length === 0 && !title) return null;

  return (
    <article className="space-y-5 rounded-2xl border border-white/10 bg-slate-950/60 p-5">
      {title && (
        <h2 className="text-lg font-semibold tracking-tight text-cyan-200">
          {title}
        </h2>
      )}

      <AnimatePresence initial={false}>
        {parts.map((item) => {
          const data = toData(item.payload?.data);

          if (item.type === "narration") {
            const text = String(data.content ?? "");
            if (!text) return null;
            return (
              <motion.p
                key={item.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="text-sm leading-relaxed text-slate-200"
              >
                {text}
              </motion.p>
            );
          }

          if (item.type === "image") {
            const src =
              typeof data.signed_url === "string"
                ? data.signed_url
                : typeof data.url === "string"
                ? data.url
                : null;
            if (!src) return null;
            return (
              <motion.figure
                key={item.id}
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
                className="overflow-hidden rounded-xl border border-white/10"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={src}
                  alt={String(data.caption ?? "AI-generated diagram")}
                  className="w-full object-cover"
                  loading="lazy"
                />
              </motion.figure>
            );
          }

          return null;
        })}
      </AnimatePresence>
    </article>
  );
}
