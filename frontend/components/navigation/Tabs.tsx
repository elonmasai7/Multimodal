"use client";

import { cn } from "@/utils/cn";

export type TabOption = { id: string; label: string };

export function Tabs({ options, active, onChange }: { options: TabOption[]; active: string; onChange: (id: string) => void }) {
  return (
    <div className="inline-flex rounded-xl border border-white/15 bg-slate-900/40 p-1" role="tablist">
      {options.map((option) => (
        <button
          key={option.id}
          onClick={() => onChange(option.id)}
          className={cn(
            "rounded-lg px-3 py-1.5 text-sm transition",
            active === option.id ? "bg-cyan-500/30 text-cyan-100" : "text-slate-300 hover:text-white"
          )}
          role="tab"
          aria-selected={active === option.id}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
