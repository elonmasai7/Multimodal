"use client";

export function ToggleControls({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className="rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-sm text-slate-100"
      aria-pressed={checked}
    >
      {label}: {checked ? "On" : "Off"}
    </button>
  );
}
