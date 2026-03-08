import { colorTokens } from "../tokens/colors";

export type LearningMode = "story" | "lesson" | "quiz";

export const themeByMode = {
  story: {
    background: colorTokens.story.background,
    surface: colorTokens.story.surface,
    primary: colorTokens.story.primary,
    accent: colorTokens.story.accent,
    secondary: colorTokens.story.secondary
  },
  lesson: {
    background: colorTokens.lesson.background,
    surface: colorTokens.lesson.surface,
    primary: colorTokens.lesson.primary,
    accent: colorTokens.lesson.accent,
    secondary: colorTokens.lesson.secondary
  },
  quiz: {
    background: colorTokens.quiz.background,
    surface: colorTokens.quiz.surface,
    primary: colorTokens.quiz.primary,
    accent: colorTokens.quiz.accent,
    secondary: colorTokens.lesson.secondary
  }
} as const;
