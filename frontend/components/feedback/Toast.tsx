export function Toast({ message }: { message: string }) {
  return <div className="rounded-xl border border-white/20 bg-slate-900/80 px-3 py-2 text-sm text-white">{message}</div>;
}
