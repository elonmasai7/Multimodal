"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { useLearningStore } from "@/store/learningStore";

function toData(payload: unknown): Record<string, unknown> {
  if (!payload || typeof payload !== "object") return {};
  return payload as Record<string, unknown>;
}

type BookPage = {
  id: string;
  type: "narration" | "image";
  text?: string;
  src?: string;
  caption?: string;
};

export type StaticBookPage = {
  type: "narration" | "image";
  content?: string;
  signed_url?: string;
  caption?: string;
};

const pageVariants = {
  enter: (dir: number) => ({
    rotateY: dir > 0 ? 25 : -25,
    x: dir > 0 ? 60 : -60,
    opacity: 0,
  }),
  center: {
    rotateY: 0,
    x: 0,
    opacity: 1,
  },
  exit: (dir: number) => ({
    rotateY: dir > 0 ? -25 : 25,
    x: dir > 0 ? -60 : 60,
    opacity: 0,
  }),
};

function TextPage({ text, pageNum }: { text: string; pageNum: number }) {
  return (
    <div className="relative flex h-full min-h-[360px] flex-col justify-between bg-[#f5f0e8] p-6 text-[#2c1810]">
      {/* Paper texture overlay */}
      <div className="pointer-events-none absolute inset-0 opacity-20"
        style={{ backgroundImage: "repeating-linear-gradient(transparent, transparent 27px, #c4a882 28px)" }}
      />
      <p className="relative z-10 font-serif text-sm leading-[1.85] tracking-wide">{text}</p>
      <span className="relative z-10 text-center text-xs text-[#8b6f47] opacity-70">{pageNum}</span>
    </div>
  );
}

function ImagePage({ src, caption }: { src: string; caption: string }) {
  return (
    <div className="relative flex h-full min-h-[360px] items-center justify-center overflow-hidden bg-black">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={caption} className="h-full w-full object-cover" />
      {caption && (
        <p className="absolute bottom-0 left-0 right-0 bg-black/60 px-3 py-1.5 text-center text-xs italic text-white/80">
          {caption}
        </p>
      )}
    </div>
  );
}

function BlankPage({ label }: { label?: string }) {
  return (
    <div className="flex h-full min-h-[360px] items-center justify-center bg-[#f5f0e8]">
      <span className="font-serif text-sm italic text-[#c4a882]">{label ?? "~ ~ ~"}</span>
    </div>
  );
}

export function StoryBook({ pages: staticPages }: { pages?: StaticBookPage[] } = {}) {
  const stream = useLearningStore((s) => s.stream);
  const [spreadIndex, setSpreadIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const prevPartsLen = useRef(0);

  // Build parts either from static saved pages or from the live stream
  const parts: BookPage[] = staticPages
    ? staticPages.map((p, i) => ({
        id: String(i),
        type: p.type,
        text: p.content,
        src: p.signed_url,
        caption: p.caption,
      }))
    : [...stream]
        .reverse()
        .filter((item) => item.type === "narration" || item.type === "image")
        .map((item) => {
          const data = toData(item.payload?.data);
          if (item.type === "narration") {
            return { id: item.id, type: "narration" as const, text: String(data.content ?? "") };
          }
          const src =
            typeof data.signed_url === "string" ? data.signed_url
            : typeof data.url === "string" ? data.url
            : undefined;
          return { id: item.id, type: "image" as const, src, caption: String(data.caption ?? "") };
        });

  const totalSpreads = Math.max(1, Math.ceil(parts.length / 2));

  // Auto-advance to the latest spread when new content arrives
  useEffect(() => {
    if (parts.length > prevPartsLen.current) {
      const latestSpread = Math.ceil(parts.length / 2) - 1;
      if (latestSpread > spreadIndex) {
        setDirection(1);
        setSpreadIndex(latestSpread);
      }
    }
    prevPartsLen.current = parts.length;
  }, [parts.length, spreadIndex]);

  if (parts.length === 0) return null;

  const leftItem = parts[spreadIndex * 2];
  const rightItem = parts[spreadIndex * 2 + 1];

  function goNext() {
    if (spreadIndex < totalSpreads - 1) {
      setDirection(1);
      setSpreadIndex((s) => s + 1);
    }
  }

  function goPrev() {
    if (spreadIndex > 0) {
      setDirection(-1);
      setSpreadIndex((s) => s - 1);
    }
  }

  function renderPage(item: BookPage | undefined, side: "left" | "right", pageNum: number) {
    if (!item) return <BlankPage label={side === "right" ? "~ End of chapter ~" : undefined} />;
    if (item.type === "narration") return <TextPage text={item.text ?? ""} pageNum={pageNum} />;
    if (item.type === "image" && item.src) return <ImagePage src={item.src} caption={item.caption ?? ""} />;
    return <BlankPage />;
  }

  const canGoPrev = spreadIndex > 0;
  const canGoNext = spreadIndex < totalSpreads - 1;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-white/10" />
        <h3 className="text-xs font-semibold uppercase tracking-widest text-amber-300/70">Story Book</h3>
        <div className="h-px flex-1 bg-white/10" />
      </div>

      {/* Book container */}
      <div className="relative" style={{ perspective: "1400px" }}>
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={spreadIndex}
            custom={direction}
            variants={pageVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.45, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ transformStyle: "preserve-3d" }}
            className="grid overflow-hidden rounded-2xl shadow-2xl shadow-black/60 lg:grid-cols-2"
          >
            {/* Left page */}
            <div
              className="cursor-pointer border-r border-[#c4a882]/30"
              onClick={goPrev}
            >
              {renderPage(leftItem, "left", spreadIndex * 2 + 1)}
            </div>

            {/* Book spine */}
            <div
              className="pointer-events-none absolute inset-y-0 left-1/2 z-10 w-px -translate-x-1/2 bg-gradient-to-b from-[#8b6f47]/40 via-[#8b6f47]/70 to-[#8b6f47]/40 shadow-[0_0_8px_2px_rgba(139,111,71,0.25)]"
              aria-hidden="true"
            />

            {/* Right page */}
            <div
              className="cursor-pointer"
              onClick={goNext}
            >
              {renderPage(rightItem, "right", spreadIndex * 2 + 2)}
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Left arrow */}
        {canGoPrev && (
          <button
            onClick={goPrev}
            aria-label="Previous page"
            className="absolute -left-4 top-1/2 z-20 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-slate-900/80 text-lg text-white shadow-lg transition-all hover:bg-slate-800 hover:scale-110"
          >
            ‹
          </button>
        )}

        {/* Right arrow */}
        {canGoNext && (
          <button
            onClick={goNext}
            aria-label="Next page"
            className="absolute -right-4 top-1/2 z-20 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-slate-900/80 text-lg text-white shadow-lg transition-all hover:bg-slate-800 hover:scale-110"
          >
            ›
          </button>
        )}
      </div>

      {/* Page indicator */}
      <div className="flex items-center justify-center gap-2">
        {Array.from({ length: totalSpreads }).map((_, i) => (
          <button
            key={i}
            onClick={() => {
              setDirection(i > spreadIndex ? 1 : -1);
              setSpreadIndex(i);
            }}
            className={`h-1.5 rounded-full transition-all ${
              i === spreadIndex ? "w-6 bg-amber-400" : "w-1.5 bg-white/20 hover:bg-white/40"
            }`}
            aria-label={`Go to spread ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
