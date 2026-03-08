import { cn } from "@/utils/cn";

export function PageContainer({
  children,
  className
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <main className={cn("mx-auto min-h-screen w-full max-w-[1400px] p-4 md:p-8", className)}>{children}</main>;
}
