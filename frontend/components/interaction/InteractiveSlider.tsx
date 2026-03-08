"use client";

export function InteractiveSlider({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <label className="block space-y-1 text-sm text-slate-200">
      <span>{label}: {value}</span>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-cyan-400"
      />
    </label>
  );
}
