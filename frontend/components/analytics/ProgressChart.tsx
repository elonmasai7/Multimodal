import { GraphViewer } from "@/components/visualization/GraphViewer";

export function ProgressChart() {
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-200">Progress Chart</h3>
      <GraphViewer values={[25, 42, 57, 63, 70, 82, 90]} />
    </section>
  );
}
