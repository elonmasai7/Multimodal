"use client";

import { useMemo, useState } from "react";

import { useLearningStore } from "@/store/learningStore";
import type { QuizPayload } from "@/types/stream";

function toData(payload: unknown): Record<string, unknown> {
  if (!payload || typeof payload !== "object") return {};
  return payload as Record<string, unknown>;
}

function shuffle<T>(arr: T[]): T[] {
  return [...arr].sort(() => Math.random() - 0.5);
}

type QuizState = "idle" | "answered";

export function StoryQuiz({ onChoice }: { onChoice?: (choice: string) => void }) {
  const stream = useLearningStore((s) => s.stream);
  const [selected, setSelected] = useState<string>("");
  const [quizState, setQuizState] = useState<QuizState>("idle");
  const [questionIndex, setQuestionIndex] = useState(0);

  // Collect all quiz events from the stream
  const quizEvents = useMemo(() => {
    return stream
      .filter((evt) => evt.type === "quiz")
      .map((evt) => {
        const data = toData(evt.payload?.data) as QuizPayload;
        return {
          id: evt.id,
          question: data.question ?? "What happened in this part of the story?",
          options: shuffle(Array.isArray(data.options) ? data.options : []),
          correct: data.correct ?? null,
        };
      });
  }, [stream]);

  if (quizEvents.length === 0) return null;

  const current = quizEvents[questionIndex % quizEvents.length];
  const isCorrect = selected === current.correct;

  function handleSubmit() {
    if (!selected) return;
    setQuizState("answered");
    onChoice?.(selected);
  }

  function handleNext() {
    setSelected("");
    setQuizState("idle");
    setQuestionIndex((i) => (i + 1) % quizEvents.length);
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-white/10" />
        <h3 className="text-xs font-semibold uppercase tracking-widest text-amber-300/70">Story Quiz</h3>
        <div className="h-px flex-1 bg-white/10" />
      </div>

      <div className="rounded-2xl border border-amber-200/20 bg-amber-500/8 p-5">
        <p className="mb-4 text-sm font-medium leading-relaxed text-amber-50">{current.question}</p>

        <div className="space-y-2">
          {current.options.map((option) => {
            const isSelected = selected === option;
            const showCorrect = quizState === "answered" && option === current.correct;
            const showWrong = quizState === "answered" && isSelected && !isCorrect;

            return (
              <button
                key={option}
                disabled={quizState === "answered"}
                onClick={() => setSelected(option)}
                className={[
                  "w-full rounded-xl border px-4 py-2.5 text-left text-sm transition-all",
                  showCorrect
                    ? "border-emerald-400/60 bg-emerald-500/20 text-emerald-100"
                    : showWrong
                    ? "border-red-400/60 bg-red-500/20 text-red-100"
                    : isSelected
                    ? "border-amber-400/60 bg-amber-500/20 text-amber-100"
                    : "border-white/15 bg-white/5 text-slate-200 hover:border-amber-300/40 hover:bg-amber-500/10",
                ].join(" ")}
              >
                {option}
                {showCorrect && " ✓"}
                {showWrong && " ✗"}
              </button>
            );
          })}
        </div>

        {quizState === "idle" && (
          <button
            onClick={handleSubmit}
            disabled={!selected}
            className="mt-4 rounded-xl bg-amber-400 px-5 py-2 text-sm font-semibold text-slate-900 transition hover:bg-amber-300 disabled:opacity-40"
          >
            Submit Answer
          </button>
        )}

        {quizState === "answered" && (
          <div className="mt-4 space-y-3">
            <p className={`text-sm font-semibold ${isCorrect ? "text-emerald-300" : "text-red-300"}`}>
              {isCorrect
                ? "Correct! Well done."
                : `Not quite — the correct answer was: ${current.correct}`}
            </p>
            {quizEvents.length > 1 && (
              <button
                onClick={handleNext}
                className="rounded-xl border border-amber-200/30 px-4 py-1.5 text-xs text-amber-200 transition hover:bg-amber-500/10"
              >
                Try another question →
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
