export type StreamEventType =
  | "status"
  | "error"
  | "narration"
  | "text"
  | "image"
  | "audio"
  | "video"
  | "quiz"
  | "simulation"
  | "done";

export type QuizOption = {
  id: string;
  label: string;
};

export type QuizPayload = {
  id: string;
  question: string;
  options: string[];
  correct?: string;
};

export type StreamPayload = {
  event_id?: string;
  timestamp?: string;
  session_type?: "story" | "lesson";
  data?: Record<string, unknown> | QuizPayload;
};

export type StreamItem = {
  id: string;
  type: StreamEventType;
  payload: StreamPayload;
};
