export type SessionKind = "story" | "lesson";

export type LearningStats = {
  completedLessons: number;
  quizAccuracy: number;
  streakDays: number;
  engagement: number;
};
