# Multimodal AI Learning Platform

Full-stack starter for an AI SaaS learning platform with:
- Interactive AI Storybooks
- Educational Explainer Lessons
- Streaming multimodal events (text/image/video/audio/quiz)

## Stack
- Frontend: Next.js 14 (App Router), TailwindCSS
- Backend: FastAPI, SSE + WebSocket endpoints
- Worker: Celery + Redis
- AI providers: Vertex AI Gemini + Imagen + Google TTS
- Data services: Firestore + Postgres + Redis
- Infra: Docker Compose + Nginx reverse proxy

## Project Structure
- `frontend/`: Next.js client apps/pages (`/dashboard`, `/story`, `/lesson`, `/teacher`)
- `backend/`: FastAPI APIs and AI orchestration mocks
- `nginx/`: reverse-proxy config
- `docker-compose.yml`: local multi-service stack

## API Endpoints (MVP)
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/story/create`
- `GET /api/v1/story/stream/{session_id}`
- `POST /api/v1/story/choice`
- `GET /api/v1/story/resume/{session_id}`
- `POST /api/v1/lesson/create`
- `GET /api/v1/lesson/stream/{lesson_id}`
- `GET /api/v1/lesson/{lesson_id}`
- `POST /api/v1/lesson/quiz`
- `GET /api/v1/lesson/progress/{lesson_id}`
- `GET /health`
- `WS /ws/stream`

All lesson/story APIs use Firebase Bearer auth when `AUTH_REQUIRED=true`.

## Run Locally (Docker)
```bash
docker compose up --build
```

Then open:
- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`
- Nginx: `http://localhost`

For local dev with no Firebase token, keep `AUTH_REQUIRED=false` and `FIRESTORE_ENABLED=false` in `backend/.env.example`.

## Backend Local Dev (without Docker)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Frontend Local Dev (without Docker)
```bash
cd frontend
npm install
npm run dev
```

## Cloud SQL Migrations
Run:

```bash
psql "$DATABASE_URL" -f backend/migrations/001_init.sql
```

## Production Notes
- Toggle `MOCK_AI=false` to enable Vertex AI + Imagen + TTS generation flow.
- Set `FIREBASE_CREDENTIALS_PATH` or run with ADC service account on Cloud Run.
- Set `GCS_MEDIA_BUCKET` and `GCS_SIGNED_URL_TTL_SECONDS` for signed media delivery.
- Ensure Cloud Run service account has `roles/storage.objectAdmin` and `roles/iam.serviceAccountTokenCreator`.
- Add rate limiting and safety filtering at the API gateway/load balancer layer.

When `MOCK_AI=false`, streamed `image` and `audio` events include:
- `gcs_uri`
- `signed_url`
