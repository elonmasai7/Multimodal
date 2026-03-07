"use client";

import { useMemo, useState } from "react";

type StreamEvent = {
  id: string;
  type: string;
  raw: string;
};

function extractPayload(raw: string): Record<string, unknown> | null {
  try {
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export default function StreamPanel({ endpoint }: { endpoint: string }) {
  const [events, setEvents] = useState<StreamEvent[]>([]);

  const startStream = () => {
    const source = new EventSource(endpoint);
    const eventTypes = ["status", "error", "narration", "text", "image", "audio", "video", "quiz", "done"];

    eventTypes.forEach((type) => {
      source.addEventListener(type, (evt) => {
        setEvents((prev) => [
          {
            id: crypto.randomUUID(),
            type,
            raw: (evt as MessageEvent).data
          },
          ...prev
        ]);
      });
    });

    source.onerror = () => {
      source.close();
    };
  };

  const rendered = useMemo(
    () =>
      events.map((event) => {
        const payload = extractPayload(event.raw);
        const data = (payload?.data ?? {}) as Record<string, unknown>;
        const imageUrl = typeof data.signed_url === "string" ? data.signed_url : typeof data.url === "string" ? data.url : null;

        const audioUrl = typeof data.signed_url === "string" ? data.signed_url : typeof data.url === "string" ? data.url : null;

        return (
          <div key={event.id} className="mb-2 rounded border border-slate-100 p-2 text-sm">
            <div className="font-semibold text-sky-700">{event.type}</div>
            {event.type === "image" && imageUrl && (
              <img src={imageUrl} alt="Generated educational visual" className="mb-2 mt-2 max-h-64 rounded border object-contain" />
            )}
            {event.type === "audio" && audioUrl && <audio controls className="my-2 w-full" src={audioUrl} />}
            <pre className="whitespace-pre-wrap break-words text-xs text-slate-600">{event.raw}</pre>
          </div>
        );
      }),
    [events]
  );

  return (
    <div className="space-y-3">
      <button
        onClick={startStream}
        className="rounded bg-sky-600 px-4 py-2 font-semibold text-white hover:bg-sky-500"
      >
        Start Stream
      </button>
      <div className="max-h-[420px] overflow-auto rounded border border-slate-200 bg-white p-3">
        {events.length === 0 && <p className="text-sm text-slate-500">No events yet.</p>}
        {rendered}
      </div>
    </div>
  );
}
