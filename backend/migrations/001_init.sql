CREATE TABLE IF NOT EXISTS student_progress (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,
  lesson_id VARCHAR(128) NOT NULL,
  score DOUBLE PRECISION NOT NULL DEFAULT 0,
  completion DOUBLE PRECISION NOT NULL DEFAULT 0,
  time_spent_seconds INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_user_lesson UNIQUE (user_id, lesson_id)
);

CREATE INDEX IF NOT EXISTS idx_student_progress_user_id ON student_progress (user_id);
CREATE INDEX IF NOT EXISTS idx_student_progress_lesson_id ON student_progress (lesson_id);
