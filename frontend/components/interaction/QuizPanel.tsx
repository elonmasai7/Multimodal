"use client";

import { useState } from "react";

export function QuizPanel({
  question,
  options,
  onSubmit
}: {
  question: string;
  options: string[];
  onSubmit: (answer: string) => void;
}) {
  const [selected, setSelected] = useState<string>("");

  return (
    <section className="rounded-2xl border border-amber-200/30 bg-amber-500/10 p-4">
      <h3 className="mb-2 text-base font-semibold text-amber-100">{question}</h3>
      <div className="mb-3 space-y-2">
        {options.map((option) => (
          <label key={option} className="flex items-center gap-2 text-sm text-amber-50">
            <input type="radio" checked={selected === option} onChange={() => setSelected(option)} />
            {option}
          </label>
        ))}
      </div>
      <button
        onClick={() => selected && onSubmit(selected)}
        className="rounded-lg bg-amber-300 px-3 py-1.5 text-sm font-semibold text-slate-900"
      >
        Submit
      </button>
    </section>
  );
}
