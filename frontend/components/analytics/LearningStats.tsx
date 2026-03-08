export function LearningStats({ stats }: { stats: Array<{ label: string; value: string }> }) {
  return (
    <div className="grid gap-3 md:grid-cols-4">
      {stats.map((item) => (
        <article key={item.label} className="rounded-2xl border border-white/15 bg-white/5 p-4">
          <h4 className="text-xs uppercase tracking-[0.12em] text-slate-300">{item.label}</h4>
          <p className="mt-1 text-2xl font-semibold text-white">{item.value}</p>
        </article>
      ))}
    </div>
  );
}
