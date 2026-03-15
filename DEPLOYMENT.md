# Msomi — GCP Deployment Reference

## Live URLs

| Service        | URL                                                                 |
|----------------|---------------------------------------------------------------------|
| Frontend       | https://msomi-frontend-922658590517.us-central1.run.app            |
| Backend API    | https://msomi-backend-922658590517.us-central1.run.app             |
| Celery Worker  | https://msomi-worker-922658590517.us-central1.run.app              |
| API Docs       | https://msomi-backend-922658590517.us-central1.run.app/docs        |
| Health Check   | https://msomi-backend-922658590517.us-central1.run.app/health      |

---

## GCP Project

| Field          | Value                          |
|----------------|--------------------------------|
| Project ID     | gen-lang-client-0347078188     |
| Region         | us-central1                    |
| Service Account| 922658590517-compute@developer.gserviceaccount.com |

---

## Infrastructure

### Artifact Registry
- **Repository**: `us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi`
- **Images**:
  - `msomi/backend:latest`
  - `msomi/frontend:latest`

### Cloud SQL (PostgreSQL)
- **Instance**: `msomi-db`
- **Edition**: Enterprise
- **Version**: PostgreSQL 16
- **Region**: us-central1
- **Database**: `modal`
- **User**: `postgres`
- **Connection name**: `gen-lang-client-0347078188:us-central1:msomi-db`

### Cloud Memorystore (Redis)
- **Instance**: `msomi-redis`
- **Private IP**: `10.104.217.51`
- **Port**: `6379`
- **Redis URL**: `redis://10.104.217.51:6379/0`

### VPC Connector
- **Name**: `msomi-vpc-connector`
- **Region**: us-central1
- **IP Range**: `10.9.0.0/28`
- Required for backend/worker to reach Redis over private IP.

---

## Secret Manager Secrets

| Secret Name          | Description                          |
|----------------------|--------------------------------------|
| `postgres-url`       | Full PostgreSQL connection URL        |
| `redis-url`          | Redis connection URL                  |
| `firebase-credentials` | Firebase Admin SDK service account JSON |
| `firebase-web-api-key` | Firebase Web API Key               |
| `db-password`        | PostgreSQL password                   |

---

## Cloud Run Services

### msomi-backend
```
gcloud run deploy msomi-backend \
  --image=us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi/backend:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --service-account=922658590517-compute@developer.gserviceaccount.com \
  --set-secrets=POSTGRES_URL=postgres-url:latest,REDIS_URL=redis-url:latest,FIREBASE_CREDENTIALS=firebase-credentials:latest,FIREBASE_WEB_API_KEY=firebase-web-api-key:latest \
  --set-env-vars=ENV=prod,API_PREFIX=/api/v1,GCP_PROJECT_ID=gen-lang-client-0347078188,GCP_REGION=us-central1,GCS_MEDIA_BUCKET=elon-fadhili,GCS_SIGNED_URL_TTL_SECONDS=3600,VERTEX_MODEL_TEXT=gemini-2.5-pro,VERTEX_MODEL_IMAGE=imagen-3.0-generate-002,VERTEX_MODEL_VIDEO=veo-3.1-generate-001,FIREBASE_PROJECT_ID=gen-lang-client-0347078188,FIREBASE_CREDENTIALS_PATH=/tmp/firebase-admin.json \
  --add-cloudsql-instances=gen-lang-client-0347078188:us-central1:msomi-db \
  --vpc-connector=msomi-vpc-connector \
  --vpc-egress=private-ranges-only \
  --min-instances=0 \
  --max-instances=5 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --project=gen-lang-client-0347078188
```

### msomi-worker
```
gcloud run deploy msomi-worker \
  --image=us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi/backend:latest \
  --platform=managed \
  --region=us-central1 \
  --no-allow-unauthenticated \
  --service-account=922658590517-compute@developer.gserviceaccount.com \
  --set-secrets=POSTGRES_URL=postgres-url:latest,REDIS_URL=redis-url:latest,FIREBASE_CREDENTIALS=firebase-credentials:latest,FIREBASE_WEB_API_KEY=firebase-web-api-key:latest \
  --set-env-vars=ENV=prod,API_PREFIX=/api/v1,GCP_PROJECT_ID=gen-lang-client-0347078188,GCP_REGION=us-central1,GCS_MEDIA_BUCKET=elon-fadhili,GCS_SIGNED_URL_TTL_SECONDS=3600,VERTEX_MODEL_TEXT=gemini-2.5-pro,VERTEX_MODEL_IMAGE=imagen-3.0-generate-002,VERTEX_MODEL_VIDEO=veo-3.1-generate-001,FIREBASE_PROJECT_ID=gen-lang-client-0347078188,FIREBASE_CREDENTIALS_PATH=/tmp/firebase-admin.json \
  --add-cloudsql-instances=gen-lang-client-0347078188:us-central1:msomi-db \
  --vpc-connector=msomi-vpc-connector \
  --vpc-egress=private-ranges-only \
  --command=python \
  --args=/app/worker_main.py \
  --min-instances=1 \
  --max-instances=2 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=3600 \
  --project=gen-lang-client-0347078188
```

### msomi-frontend
```
gcloud run deploy msomi-frontend \
  --image=us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi/frontend:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars=NEXT_PUBLIC_API_BASE=https://msomi-backend-922658590517.us-central1.run.app/api/v1 \
  --min-instances=0 \
  --max-instances=3 \
  --memory=512Mi \
  --cpu=1 \
  --port=3000 \
  --project=gen-lang-client-0347078188
```

---

## Redeployment (after code changes)

### Backend / Worker
```
# Rebuild and push
docker build -t us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi/backend:latest backend
docker push us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi/backend:latest

# Redeploy (image only, keeps existing config)
gcloud run deploy msomi-backend --image=us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi/backend:latest --region=us-central1 --project=gen-lang-client-0347078188
gcloud run deploy msomi-worker --image=us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi/backend:latest --region=us-central1 --project=gen-lang-client-0347078188
```

### Frontend
```
# Rebuild and push
docker build -t us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi/frontend:latest frontend
docker push us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi/frontend:latest

# Redeploy
gcloud run deploy msomi-frontend --image=us-central1-docker.pkg.dev/gen-lang-client-0347078188/msomi/frontend:latest --region=us-central1 --project=gen-lang-client-0347078188
```

### Re-authenticate Docker (if push fails)
```
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin us-central1-docker.pkg.dev
```

---

## IAM Roles (service account)

The Compute Engine default service account (`922658590517-compute@developer.gserviceaccount.com`) has been granted:
- `roles/aiplatform.user` — Vertex AI access
- `roles/storage.objectAdmin` — GCS bucket access
- `roles/secretmanager.secretAccessor` — Secret Manager access
- `roles/cloudsql.client` — Cloud SQL access
