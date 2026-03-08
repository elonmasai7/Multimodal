export function Notification({ title, detail }: { title: string; detail: string }) {
  return (
    <div role="status" className="rounded-2xl border border-emerald-200/30 bg-emerald-500/10 p-3">
      <h4 className="text-sm font-semibold text-emerald-100">{title}</h4>
      <p className="text-xs text-emerald-50">{detail}</p>
    </div>
  );
}
