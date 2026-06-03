# Msomi; an AI Creative Storyteller & Learning Platform

Msomi is a multimodal AI agent that generates immersive storybooks and educational explainers by weaving **text, inline images, audio narration, and video** in a single streaming response breaking the "text box" paradigm.

**Live Demo**: https://msomi-frontend-922658590517.us-central1.run.app

> **Note for Judges**: The live demo runs on a shared GCP project with Vertex AI quota limits. During periods of high usage (concurrent Veo video generation, Gemini calls), the backend may return transient `503` or `429` errors. If the live demo is unavailable or slow, we recommend **reproducing the project locally or on your own GCP project** using the step-by-step instructions below — the full setup takes approximately 20–30 minutes.

---

## What Makes It Different

Most AI apps work in turns: you ask, it answers. Msomi works like a **creative director**:

1. A single Gemini call with `response_modalities=["TEXT","IMAGE"]` produces a narrative where text paragraphs and inline illustrations flow together using Gemini's native interleaved output.
2. While the text streams to the user, Veo video generation and Google TTS audio run concurrently.
3. The result is a live, context-aware experience: text → inline image → text → inline image → narration audio → video — all in one fluid SSE stream.

## Current Direction

- **Image generation provider**: Qwen Image is the target provider for generated visuals.
- **Cloud provider**: Azure is the target production cloud.
- **Migration note**: The repository still contains legacy Google Cloud/Vertex AI/Imagen/GCS deployment and runtime hooks. Treat those as existing implementation details until an Azure + Qwen provider migration is completed, not as the desired future production direction.

Target production deployment should be on Azure. Legacy GCP setup and deployment commands remain below for reference only until Azure infrastructure-as-code and deployment automation are added.

For **Story mode**, the agent tracks choices across scenes, building a branching narrative grounded in prior context.

---

## Architecture

```
User Browser
     │  SSE stream (text/image/audio/video/quiz events)
     ▼
┌─────────────────────────────────────────────────────┐
│               Frontend (Next.js 14)                 │
│  Cloud Run · us-central1                            │
│  useSSEStream → learningStore → StreamRenderer      │
└──────────────────────┬──────────────────────────────┘
                       │ REST + SSE
                       ▼
┌─────────────────────────────────────────────────────┐
│               Backend API (FastAPI)                 │
│  Cloud Run · us-central1 · timeout=1800s            │
│                                                     │
│  stream_multimodal_events()                         │
│  ┌─────────────────────────────────────────────┐   │
│  │ Step 1: Gemini interleaved call             │   │
│  │   model: gemini-2.0-flash-preview-image-    │   │
│  │          generation                         │   │
│  │   modalities: [TEXT, IMAGE]                 │   │
│  │   → narration paragraphs + inline images    │   │
│  │   → title, video_prompt, quiz metadata      │   │
│  │                                             │   │
│  │ Step 2: Stream interleaved parts via SSE    │   │
│  │                                             │   │
│  │ Step 3: Launch Veo video (async task)       │   │
│  │   story → veo-3.0-fast-generate-001         │   │
│  │   lesson → veo-3.1-generate-001             │   │
│  │   keepalive SSE every 20s during generation │   │
│  │                                             │   │
│  │ Step 4: Google TTS audio (concurrent)       │   │
│  │                                             │   │
│  │ Step 5: Await video + emit SSE event        │   │
│  │                                             │   │
│  │ Step 6: Quiz event                          │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Firebase Auth · Firestore · Redis cache            │
└──┬──────────────┬──────────────┬───────────────────┘
   │              │              │
   ▼              ▼              ▼
Vertex AI      Google TTS    Cloud Storage (GCS)
Gemini 2.5     en-US-         Signed URLs for
Imagen 3.0     Neural2-C      images / audio / video
Veo 3.x
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TailwindCSS, Framer Motion, Zustand, React Three Fiber |
| Backend | FastAPI, Python 3.12, asyncio, SSE streaming |
| AI — Text + Images | `gemini-2.0-flash-preview-image-generation` (interleaved output) |
| AI — Text only | `gemini-2.5-pro` (lesson plan with Google Search grounding) |
| AI — Images | Qwen Image target; current legacy path uses `imagen-3.0-generate-002` |
| AI — Video | `veo-3.1-generate-001` (lesson), `veo-3.0-fast-generate-001` (story) |
| AI — Audio | Google Cloud Text-to-Speech (`en-US-Neural2-C`) |
| Auth | Firebase Authentication + Firebase Admin SDK |
| Database | Cloud SQL (PostgreSQL 16) + Cloud Firestore |
| Cache | Cloud Memorystore (Redis) |
| Storage | Azure Blob target; current legacy path uses Google Cloud Storage (GCS) with IAM-signed URLs |
| Infra | Azure target; current legacy deployment uses Google Cloud Run, Artifact Registry, Secret Manager, VPC Connector |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install)
- [Node.js 18+](https://nodejs.org/) (for local frontend dev only)
- A GCP project with billing enabled
- A Firebase project (can be the same GCP project)

---

## Local Development

### 1. Clone the repo

```bash
git clone <repo-url>
cd Multimodal
```

### 2. Configure backend environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your values:

```env
GCP_PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1
GCS_MEDIA_BUCKET=your-gcs-bucket-name

FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_WEB_API_KEY=your-firebase-web-api-key
FIREBASE_CREDENTIALS_PATH=/app/credentials/firebase-admin.json

VERTEX_MODEL_TEXT=gemini-2.5-pro
VERTEX_MODEL_IMAGE=imagen-3.0-generate-002
VERTEX_MODEL_VIDEO=veo-3.1-generate-001
VERTEX_MODEL_VIDEO_STORY=veo-3.0-fast-generate-001
```

### 3. Add Firebase service account credentials

Download your Firebase Admin SDK JSON from:
**Firebase Console → Project Settings → Service Accounts → Generate new private key**

Place it at: `backend/credentials/firebase-admin.json`

### 4. Configure frontend environment

```bash
cp frontend/.env.example frontend/.env.local
```

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```

### 5. Run with Docker Compose

```bash
docker compose up --build
```

Services started:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redis: localhost:6379
- PostgreSQL: localhost:5432

### 6. Demo login (no Firebase required locally)

```
Email: demo@example.com
Password: demo12345
```

---

## GCP Setup (First-time)

### Step 1 — Authenticate and set project

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### Step 2 — Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  texttospeech.googleapis.com \
  storage.googleapis.com \
  firestore.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  vpcaccess.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com
```

### Step 3 — Grant IAM roles to the Compute service account

```bash
SA="$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:$SA" --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:$SA" --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:$SA" --role="roles/iam.serviceAccountTokenCreator"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:$SA" --role="roles/cloudsql.client"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:$SA" --role="roles/datastore.user"
```

> `roles/iam.serviceAccountTokenCreator` is required for GCS signed URL generation from Cloud Run.

### Step 4 — Create GCS bucket (same region as Cloud Run)

```bash
gcloud storage buckets create gs://YOUR_BUCKET_NAME --location=us-central1
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET_NAME \
  --member="serviceAccount:$SA" --role="roles/storage.objectAdmin"
```

### Step 5 — Create Artifact Registry

```bash
gcloud artifacts repositories create msomi \
  --repository-format=docker \
  --location=us-central1
```

### Step 6 — Create Cloud SQL (PostgreSQL)

```bash
gcloud sql instances create msomi-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1

gcloud sql databases create modal --instance=msomi-db
gcloud sql users set-password postgres --instance=msomi-db --password=YOUR_DB_PASSWORD
```

### Step 7 — Create Cloud Memorystore (Redis)

```bash
gcloud redis instances create msomi-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0

# Get the private IP
gcloud redis instances describe msomi-redis --region=us-central1 --format="value(host,port)"
```

### Step 8 — Create VPC connector (for Redis private access)

```bash
gcloud compute networks vpc-access connectors create msomi-connector \
  --region=us-central1 \
  --network=default \
  --range=10.9.0.0/28
```

### Step 9 — Store secrets in Secret Manager

```bash
# PostgreSQL URL
echo -n "postgresql+asyncpg://postgres:YOUR_DB_PASSWORD@/modal?host=/cloudsql/YOUR_PROJECT:us-central1:msomi-db" | \
  gcloud secrets create postgres-url --data-file=-

# Firebase credentials (service account JSON)
gcloud secrets create firebase-credentials --data-file=backend/credentials/firebase-admin.json

# Firebase Web API Key
echo -n "YOUR_FIREBASE_WEB_API_KEY" | gcloud secrets create firebase-web-api-key --data-file=-
```

---

## Cloud Deployment

### Build and push Docker images

```bash
REGISTRY=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/msomi

# Authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Backend
docker build -t $REGISTRY/backend:latest backend
docker push $REGISTRY/backend:latest

# Frontend
docker build -t $REGISTRY/frontend:latest frontend
docker push $REGISTRY/frontend:latest
```

### Deploy backend to Cloud Run

```bash
gcloud run deploy msomi-backend \
  --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/msomi/backend:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-secrets="POSTGRES_URL=postgres-url:latest,FIREBASE_CREDENTIALS=firebase-credentials:latest,FIREBASE_WEB_API_KEY=firebase-web-api-key:latest" \
  --set-env-vars="GCP_PROJECT_ID=YOUR_PROJECT_ID,GCP_REGION=us-central1,GCS_MEDIA_BUCKET=YOUR_BUCKET,FIREBASE_PROJECT_ID=YOUR_PROJECT_ID,FIREBASE_CREDENTIALS_PATH=/app/credentials/firebase-admin.json,VERTEX_MODEL_TEXT=gemini-2.5-pro,VERTEX_MODEL_IMAGE=imagen-3.0-generate-002,VERTEX_MODEL_VIDEO=veo-3.1-generate-001,VERTEX_MODEL_VIDEO_STORY=veo-3.0-fast-generate-001,REDIS_URL=redis://REDIS_IP:6379/0" \
  --add-cloudsql-instances=YOUR_PROJECT_ID:us-central1:msomi-db \
  --vpc-connector=msomi-connector \
  --vpc-egress=private-ranges-only \
  --timeout=1800 \
  --min-instances=1 \
  --max-instances=10 \
  --memory=2Gi \
  --cpu=2 \
  --project=YOUR_PROJECT_ID
```

> `--timeout=1800`: Required — Veo video generation takes up to 5 minutes. The backend sends SSE keepalive comments every 20s to prevent browser disconnection during this wait.
> `--min-instances=1`: Eliminates cold-start 503s.

### Deploy frontend to Cloud Run

```bash
BACKEND_URL=$(gcloud run services describe msomi-backend --region=us-central1 --format="value(status.url)")

gcloud run deploy msomi-frontend \
  --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/msomi/frontend:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="NEXT_PUBLIC_API_BASE=$BACKEND_URL/api/v1" \
  --min-instances=1 \
  --max-instances=5 \
  --memory=512Mi \
  --cpu=1 \
  --port=3000 \
  --project=YOUR_PROJECT_ID
```

### Redeployment (after code changes)

```bash
REGISTRY=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/msomi

# Backend
docker build -t $REGISTRY/backend:latest backend && docker push $REGISTRY/backend:latest
gcloud run deploy msomi-backend --image=$REGISTRY/backend:latest --region=us-central1 --project=YOUR_PROJECT_ID

# Frontend
docker build -t $REGISTRY/frontend:latest frontend && docker push $REGISTRY/frontend:latest
gcloud run deploy msomi-frontend --image=$REGISTRY/frontend:latest --region=us-central1 --project=YOUR_PROJECT_ID
```

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `CLOUD_PROVIDER` | No | Runtime cloud direction, default `azure`; current media path logs fallback to legacy GCP until Azure adapters are implemented |
| `IMAGE_GENERATION_PROVIDER` | No | Runtime image provider direction, default `qwen`; current image path logs fallback to Vertex/Imagen until Qwen adapter is implemented |
| `MEDIA_STORAGE_PROVIDER` | No | Runtime media storage direction, default `azure_blob`; current media path logs fallback to GCS until Azure Blob adapter is implemented |
| `QWEN_API_KEY` | Target | Qwen image provider credential once the adapter is implemented |
| `QWEN_IMAGE_ENDPOINT` | Target | Qwen image provider endpoint once the adapter is implemented |
| `QWEN_IMAGE_MODEL` | Target | Qwen image model name, default `qwen-image` |
| `AZURE_STORAGE_CONNECTION_STRING` | Target | Azure Blob credential/config once storage migration is implemented |
| `AZURE_STORAGE_ACCOUNT_URL` | Target | Azure Storage account URL once storage migration is implemented |
| `AZURE_MEDIA_CONTAINER` | Target | Azure Blob media container, default `media` |
| `AZURE_SIGNED_URL_TTL_SECONDS` | Target | Azure SAS URL TTL, default `3600` |
| `GCP_PROJECT_ID` | Yes | GCP project ID |
| `GCP_REGION` | Yes | GCP region (e.g. `us-central1`) |
| `GCS_MEDIA_BUCKET` | Yes | GCS bucket for media uploads |
| `VERTEX_MODEL_TEXT` | Yes | Gemini text model (`gemini-2.5-pro`) |
| `VERTEX_MODEL_IMAGE` | Yes | Imagen model (`imagen-3.0-generate-002`) |
| `VERTEX_MODEL_VIDEO` | Yes | Veo model for lessons (`veo-3.1-generate-001`) |
| `VERTEX_MODEL_VIDEO_STORY` | No | Veo model for story mode — uses faster model (`veo-3.0-fast-generate-001`) |
| `FIREBASE_PROJECT_ID` | Yes | Firebase project ID |
| `FIREBASE_WEB_API_KEY` | Yes | Firebase Web API key (for client auth) |
| `FIREBASE_CREDENTIALS_PATH` | Yes | Path to Firebase Admin SDK JSON |
| `FIREBASE_CREDENTIALS` | Cloud only | Firebase Admin SDK JSON content (written to path at startup) |
| `POSTGRES_URL` | Yes | PostgreSQL connection URL (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Yes | Redis URL (`redis://host:6379/0`) |
| `DEMO_AUTH_EMAIL` | No | Demo login email (default: `demo@example.com`) |
| `DEMO_AUTH_PASSWORD` | No | Demo login password (default: `demo12345`) |

---

## How the Multimodal Pipeline Works

### Mandatory Tech: Gemini Interleaved Output

The core of Msomi is a **single Gemini API call** that produces mixed text and images:

```python
response = genai.models.generate_content(
    model="gemini-2.0-flash-preview-image-generation",
    contents=prompt,
    config=GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        temperature=0.7,
    ),
)
# Response parts: [text, image, text, image, text, ...]
```

Each text part is a narration paragraph. Each image part is a base64-encoded inline illustration. They arrive interleaved in the response — one model call, one coherent creative output.

### Grounding (Anti-hallucination)

Lesson content uses Google Search grounding to ensure factual accuracy:

```python
config = GenerateContentConfig(
    tools=[Tool(google_search=GoogleSearch())],
    temperature=0.3,  # low temperature = high-confidence tokens only
)
```

### SSE Streaming Architecture

The backend streams Server-Sent Events in this sequence:

```
event: status   → "Weaving text and visuals with Gemini…"
event: text     → lesson title + full narration text
event: narration → paragraph 1 (from interleaved stream)
event: image    → inline image 1 (GCS signed URL)
event: narration → paragraph 2
event: image    → inline image 2
event: status   → "Generating Veo video…"
: keepalive     ← SSE comment every 20s during Veo generation
event: audio    → narration audio (GCS signed URL)
event: video    → Veo video (GCS signed URL)
event: quiz     → quiz question + options
event: done     → generation complete
```

### Story Mode — Context-Aware Branching

Story sessions persist choices in Firestore. Each subsequent scene call includes prior context, so the narrative adapts to user decisions across scenes.

---

## API Reference

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/signup` | Create account |
| POST | `/api/v1/auth/login` | Login (returns Firebase ID token) |
| POST | `/api/v1/auth/refresh` | Refresh token |
| POST | `/api/v1/auth/demo` | Demo login (dev only) |
| GET | `/api/v1/auth/session` | Get current user |

### Story
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/story/create` | Create story session |
| GET | `/api/v1/story/stream/{session_id}` | SSE stream (pass token as query param) |
| POST | `/api/v1/story/choice` | Submit scene choice |
| GET | `/api/v1/story/resume/{session_id}` | Resume session state |
| GET | `/api/v1/story/sessions` | List user's story sessions |

### Lesson
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/lesson/create` | Create lesson session |
| GET | `/api/v1/lesson/stream/{lesson_id}` | SSE stream |
| GET | `/api/v1/lesson/{lesson_id}` | Get lesson data |
| POST | `/api/v1/lesson/quiz` | Submit quiz answer |

### System
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/docs` | OpenAPI docs (Swagger UI) |

---

## Viewing Logs

```bash
# Live logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=msomi-backend" \
  --limit=50 --project=YOUR_PROJECT_ID --format="value(timestamp,textPayload)" --freshness=10m

# Errors only
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=msomi-backend AND severity>=ERROR" \
  --limit=20 --project=YOUR_PROJECT_ID --format=json --freshness=1h
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `503` on story/create | `REDIS_URL` not set on Cloud Run | Set `REDIS_URL=redis://REDIS_IP:6379/0` |
| Images not loading | GCS signed URL failure (ADC can't sign locally) | Ensure `roles/iam.serviceAccountTokenCreator` is granted |
| Video never arrives | SSE connection dropped during Veo generation | Backend sends keepalive every 20s; frontend only hard-closes on `CLOSED` state |
| Cold-start 503s | Cloud Run scales to 0 | Set `--min-instances=1` |
| `inline_image_upload_failed` | Wrong GCS bucket region | Use a bucket in the same region as Cloud Run |
| Firebase init fails | `FIREBASE_CREDENTIALS` secret not mounted | Add `--set-secrets=FIREBASE_CREDENTIALS=firebase-credentials:latest` |

## Notes

- SSE streaming endpoints accept Firebase bearer token in `Authorization` or query param `token` (for native `EventSource`).
- Target direction is Qwen-generated images stored in Azure Blob Storage and returned as short-lived SAS URLs. The current legacy implementation uploads generated image/audio assets to GCS and returns signed URLs.
- Video generation uses configured VideoFX endpoint.
