const mockStats = [
  { metric: "Lesson completion", value: "78%" },
  { metric: "Average score", value: "84" },
  { metric: "Hardest topic", value: "Cellular respiration" }
];

export default function TeacherPage() {
  return (
    <main className="space-y-4">
      <h1 className="text-3xl font-bold">Teacher Dashboard</h1>
      <div className="grid gap-3 md:grid-cols-3">
        {mockStats.map((item) => (
          <article key={item.metric} className="rounded border border-slate-200 bg-white p-4">
            <h2 className="text-sm text-slate-500">{item.metric}</h2>
            <p className="text-2xl font-bold">{item.value}</p>
          </article>
        ))}
      </div>
    </main>
  );
}
