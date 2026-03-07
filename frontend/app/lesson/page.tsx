import StreamPanel from "@/components/StreamPanel";

export default function LessonPage() {
  const endpoint = "http://localhost:8000/api/v1/lesson/stream/demo?prompt=Explain+photosynthesis+for+high+school";

  return (
    <main className="space-y-4">
      <h1 className="text-3xl font-bold">Lesson Viewer</h1>
      <p className="text-slate-700">Streams lesson narration, generated visuals, short video snippets, and quiz events.</p>
      <StreamPanel endpoint={endpoint} />
    </main>
  );
}
