import { cn } from "@/utils/cn";

export function Sidebar({ title, children, className }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <aside className={cn("rounded-2xl border border-white/15 bg-white/5 p-4 backdrop-blur-sm", className)}>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.16em] text-cyan-200">{title}</h2>
      {children}
    </aside>
  );
}
