import { GraphViewer } from "@/components/visualization/GraphViewer";

export function ProgressChart({ values, labels }: { values: number[]; labels?: string[] }) {
  const display = values.length > 0 ? values : [];
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-200">Quiz Score History</h3>
      {display.length === 0 ? (
        <p className="text-xs text-slate-500">No quiz scores yet.</p>
      ) : (
        <>
          <GraphViewer values={display} />
          {labels && labels.length > 0 && (
            <div className="flex gap-1 overflow-x-auto">
              {labels.map((l, i) => (
                <span key={i} className="shrink-0 truncate text-[10px] text-slate-500 max-w-[80px]">{l}</span>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
