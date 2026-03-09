export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";
export const DEMO_LOGIN_EMAIL = process.env.NEXT_PUBLIC_DEMO_LOGIN_EMAIL ?? "demo@modal.local";
export const DEMO_LOGIN_PASSWORD = process.env.NEXT_PUBLIC_DEMO_LOGIN_PASSWORD ?? "demo12345";

export type AuthPayload = {
  id_token: string;
  refresh_token: string | null;
  user_id: string | null;
  email: string | null;
};

async function parseResponse(res: Response) {
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const validationErrors = Array.isArray(body?.details?.errors) ? body.details.errors : [];
    const validationMessage =
      validationErrors.length > 0 ? validationErrors.map((error: { msg?: string }) => error.msg).filter(Boolean).join(", ") : null;
    throw new Error(validationMessage ?? body?.message ?? body?.detail ?? `Request failed: ${res.status}`);
  }
  return body;
}

export async function signup(email: string, password: string, displayName?: string): Promise<AuthPayload> {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, display_name: displayName })
  });
  const body = await parseResponse(res);
  return body.data as AuthPayload;
}

export async function login(email: string, password: string): Promise<AuthPayload> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const body = await parseResponse(res);
  return body.data as AuthPayload;
}

export async function getSession(token: string) {
  const res = await fetch(`${API_BASE}/auth/session`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return parseResponse(res);
}

export async function createSession(prompt: string, sessionType: "story" | "lesson", token: string) {
  const route = sessionType === "story" ? "story/create" : "lesson/create";
  const res = await fetch(`${API_BASE}/${route}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ prompt, session_type: sessionType, duration: 10 })
  });
  return parseResponse(res);
}

export async function submitStoryChoice(token: string, payload: { session_id: string; scene_id: string; choice_text: string }) {
  const res = await fetch(`${API_BASE}/story/choice`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
  return parseResponse(res);
}

export async function resumeStory(token: string, sessionId: string) {
  const res = await fetch(`${API_BASE}/story/resume/${sessionId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return parseResponse(res);
}

export async function getLesson(token: string, lessonId: string) {
  const res = await fetch(`${API_BASE}/lesson/${lessonId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return parseResponse(res);
}

export async function submitLessonQuiz(
  token: string,
  payload: { lesson_id: string; question_id: string; answer: string; time_spent_seconds: number }
) {
  const res = await fetch(`${API_BASE}/lesson/quiz`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
  return parseResponse(res);
}

export async function getLessonProgress(token: string, lessonId: string) {
  const res = await fetch(`${API_BASE}/lesson/progress/${lessonId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return parseResponse(res);
}

export async function getStudentProgressAnalytics(token: string, userId?: string) {
  const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
  const res = await fetch(`${API_BASE}/analytics/student-progress${query}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return parseResponse(res);
}

export async function getLessonPerformanceAnalytics(token: string) {
  const res = await fetch(`${API_BASE}/analytics/lesson-performance`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return parseResponse(res);
}

export function storyStreamUrl(sessionId: string, prompt: string, token: string) {
  return `${API_BASE}/story/stream/${sessionId}?prompt=${encodeURIComponent(prompt)}&token=${encodeURIComponent(token)}`;
}

export function lessonStreamUrl(lessonId: string, prompt: string, token: string) {
  return `${API_BASE}/lesson/stream/${lessonId}?prompt=${encodeURIComponent(prompt)}&token=${encodeURIComponent(token)}`;
}
