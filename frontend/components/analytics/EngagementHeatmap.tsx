const data = [12, 8, 19, 5, 14, 20, 17, 3, 11, 16, 22, 9];

export function EngagementHeatmap() {
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-fuchsia-200">Engagement Heatmap</h3>
      <div className="grid grid-cols-6 gap-2">
        {data.map((value, idx) => (
          <div
            key={idx}
            className="h-10 rounded-md"
            style={{ backgroundColor: `rgba(167, 139, 250, ${Math.min(0.15 + value / 25, 1)})` }}
            aria-label={`Engagement ${value}`}
          />
        ))}
      </div>
    </section>
  );
}
