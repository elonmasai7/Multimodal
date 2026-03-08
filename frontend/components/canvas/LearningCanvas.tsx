import { CanvasLayout } from "@/components/layout/CanvasLayout";

export function LearningCanvas({ children }: { children: React.ReactNode }) {
  return <CanvasLayout className="min-h-[460px]">{children}</CanvasLayout>;
}
