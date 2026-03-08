export function GraphViewer({ values }: { values: number[] }) {
  return (
    <div className="rounded-2xl border border-white/15 bg-slate-900/50 p-3">
      <div className="flex h-28 items-end gap-2">
        {values.map((value, idx) => (
          <div key={idx} className="w-full rounded-t bg-cyan-300/80" style={{ height: `${value}%` }} />
        ))}
      </div>
    </div>
  );
}
