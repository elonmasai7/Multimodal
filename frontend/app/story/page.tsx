import StreamPanel from "@/components/StreamPanel";

export default function StoryPage() {
  const endpoint = "http://localhost:8000/api/v1/story/stream/demo?prompt=Pirate+adventure+teaching+teamwork";

  return (
    <main className="space-y-4">
      <h1 className="text-3xl font-bold">Interactive Story Player</h1>
      <p className="text-slate-700">Streams narration, images, video cues, and quiz choices for branching story content.</p>
      <StreamPanel endpoint={endpoint} />
    </main>
  );
}
