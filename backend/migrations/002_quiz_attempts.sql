CREATE TABLE IF NOT EXISTS lesson_quiz_attempts (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,
  lesson_id VARCHAR(128) NOT NULL,
  question_id VARCHAR(128) NOT NULL,
  answer VARCHAR(256) NOT NULL,
  correct BOOLEAN NOT NULL,
  time_spent_seconds INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user ON lesson_quiz_attempts (user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_lesson ON lesson_quiz_attempts (lesson_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_question ON lesson_quiz_attempts (question_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_correct ON lesson_quiz_attempts (correct);
