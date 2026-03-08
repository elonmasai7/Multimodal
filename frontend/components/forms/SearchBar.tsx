"use client";

export function SearchBar({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Search lessons, skills, students"
      className="w-full rounded-xl border border-white/20 bg-slate-900/60 px-3 py-2 text-sm text-white"
      aria-label="Search"
    />
  );
}
