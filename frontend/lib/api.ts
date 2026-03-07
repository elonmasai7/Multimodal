export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";
const DEMO_TOKEN = process.env.NEXT_PUBLIC_FIREBASE_TOKEN;

export async function createSession(prompt: string, sessionType: "story" | "lesson") {
  const route = sessionType === "story" ? "story/create" : "lesson/create";
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (DEMO_TOKEN) headers.Authorization = `Bearer ${DEMO_TOKEN}`;

  const res = await fetch(`${API_BASE}/${route}`, {
    method: "POST",
    headers,
    body: JSON.stringify({ prompt, session_type: sessionType, duration: 10 })
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}
