"use client";

import { useState } from "react";
import { createSession } from "@/lib/api";

export default function DashboardPage() {
  const [prompt, setPrompt] = useState("Explain the solar system for middle school");
  const [result, setResult] = useState<string>("");

  const run = async (sessionType: "story" | "lesson") => {
    const res = await createSession(prompt, sessionType);
    setResult(JSON.stringify(res, null, 2));
  };

  return (
    <main className="space-y-4">
      <h1 className="text-3xl font-bold">Student Dashboard</h1>
      <textarea className="w-full rounded border p-3" rows={4} value={prompt} onChange={(e) => setPrompt(e.target.value)} />
      <div className="space-x-2">
        <button onClick={() => run("story")} className="rounded bg-slate-800 px-4 py-2 text-white">Create Story</button>
        <button onClick={() => run("lesson")} className="rounded bg-sky-600 px-4 py-2 text-white">Create Lesson</button>
      </div>
      <pre className="rounded bg-white p-3 text-xs">{result || "API response will appear here."}</pre>
    </main>
  );
}
