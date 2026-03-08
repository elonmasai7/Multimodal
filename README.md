# Multimodal AI Learning Platform

Production-oriented full-stack AI learning platform:
- Interactive AI storybooks
- Adaptive educational explainers
- Live multimodal streaming (text, image, video, audio, quiz)

## Stack
- Frontend: Next.js 14, TailwindCSS, Framer Motion, Zustand, React Spring, React Three Fiber
- Backend: FastAPI, Firebase Auth, Firestore, Cloud SQL (Postgres), Redis, Vertex AI, Imagen, VideoFX, Google TTS
- Worker: Celery + Redis
- Infra: Docker Compose + Nginx

## API Endpoints
Authentication:
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/session`

Story:
- `POST /api/v1/story/create`
- `GET /api/v1/story/stream/{session_id}`
- `POST /api/v1/story/choice`
- `GET /api/v1/story/resume/{session_id}`

Lesson:
- `POST /api/v1/lesson/create`
- `GET /api/v1/lesson/stream/{lesson_id}`
- `GET /api/v1/lesson/{lesson_id}`
- `POST /api/v1/lesson/quiz`
- `GET /api/v1/lesson/progress/{lesson_id}`
- `GET /api/v1/lesson/progress?lesson_id={lesson_id}`

Analytics:
- `GET /api/v1/analytics/student-progress`
- `GET /api/v1/analytics/lesson-performance`

System:
- `GET /health`
- `WS /ws/stream`

## Required Configuration
Set these in backend `.env`:
- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCS_MEDIA_BUCKET`
- `VERTEX_MODEL_TEXT`
- `VERTEX_MODEL_IMAGE`
- `VIDEOFX_ENDPOINT`
- `VIDEOFX_API_KEY` (if required by your provider)
- `FIREBASE_PROJECT_ID`
- `FIREBASE_WEB_API_KEY`
- `FIREBASE_CREDENTIALS_PATH` (or ADC in Cloud Run)
- `POSTGRES_URL`
- `REDIS_URL`

## Deployment Readiness Check
Before startup, run:

```bash
./scripts/deployment-readiness.sh
```

The checker validates:
- required env vars
- Redis and Postgres connectivity
- Firestore connectivity
- GCS bucket reachability and IAM permissions
- signed URL capability (`roles/iam.serviceAccountTokenCreator`)
- Vertex Gemini and Imagen access
- VideoFX endpoint reachability
- Firebase Admin and Firebase Web API accessibility

Docker Compose backend/worker now run this readiness check automatically before service startup.

## Cloud SQL Migrations
```bash
psql "$DATABASE_URL" -f backend/migrations/001_init.sql
psql "$DATABASE_URL" -f backend/migrations/002_quiz_attempts.sql
```

## Run Locally
```bash
docker compose up --build
```

## Notes
- SSE streaming endpoints accept Firebase bearer token in `Authorization` or query param `token` (for native `EventSource`).
- Generated image/audio assets are uploaded to GCS and returned as signed URLs.
- Video generation uses configured VideoFX endpoint.
