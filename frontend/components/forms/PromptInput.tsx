"use client";

export function PromptInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <label className="block space-y-2">
      <span className="text-xs uppercase tracking-[0.12em] text-slate-300">Learning prompt</span>
      <textarea
        rows={3}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-2xl border border-white/20 bg-slate-950/70 p-3 text-sm text-white outline-none focus:border-cyan-300"
      />
    </label>
  );
}
