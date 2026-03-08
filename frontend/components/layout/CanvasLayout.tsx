import { cn } from "@/utils/cn";

export function CanvasLayout({
  children,
  className
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "relative overflow-hidden rounded-[28px] border border-white/15 bg-[radial-gradient(circle_at_top,rgba(103,232,249,0.2),transparent_60%),radial-gradient(circle_at_bottom,rgba(167,139,250,0.25),transparent_55%),rgba(2,6,23,0.9)] p-4 shadow-[0_30px_80px_rgba(0,0,0,0.5)] md:p-6",
        className
      )}
    >
      {children}
    </section>
  );
}
