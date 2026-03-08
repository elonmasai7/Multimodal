import { cn } from "@/utils/cn";

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return <article className={cn("rounded-2xl border border-white/15 bg-white/5 p-4 backdrop-blur-md", className)}>{children}</article>;
}
