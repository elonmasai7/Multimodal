// completion values 0–1 per lesson, mapped to violet opacity
export function EngagementHeatmap({ completions, labels }: { completions: number[]; labels?: string[] }) {
  if (completions.length === 0) {
    return (
      <section className="space-y-2">
        <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-fuchsia-200">Watch Engagement</h3>
        <p className="text-xs text-slate-500">No watch data yet.</p>
      </section>
    );
  }
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-fuchsia-200">Watch Engagement</h3>
      <div className="grid grid-cols-6 gap-2">
        {completions.map((value, idx) => {
          const pct = Math.min(1, Math.max(0, value));
          const label = labels?.[idx] ?? `Lesson ${idx + 1}`;
          const cls =
            pct >= 0.85
              ? "h-10 rounded-md bg-emerald-400/70"
              : pct >= 0.4
              ? "h-10 rounded-md bg-amber-400/60"
              : "h-10 rounded-md bg-violet-400/30";
          return (
            <div
              key={idx}
              className={cls}
              title={`${label}: ${Math.round(pct * 100)}% watched`}
            />
          );
        })}
      </div>
      <div className="flex gap-3 text-[10px] text-slate-400">
        <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />Watched all</span>
        <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-amber-400" />Half</span>
        <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-violet-400" />Low</span>
      </div>
    </section>
  );
}
