import mimetypes
import os
import uuid
from dataclasses import dataclass
from datetime import timedelta

from google.cloud import storage

from app.core.config import settings


@dataclass
class UploadedMedia:
    gcs_uri: str
    signed_url: str
    content_type: str
    blob_name: str


class GCSMediaService:
    def __init__(self) -> None:
        if not settings.gcs_media_bucket:
            raise RuntimeError("GCS_MEDIA_BUCKET is required for media uploads")
        self.client = storage.Client(project=settings.gcp_project_id or None)
        self.bucket = self.client.bucket(settings.gcs_media_bucket)

    def upload_file_and_sign(self, *, local_path: str, prefix: str, content_type: str | None = None) -> UploadedMedia:
        ext = os.path.splitext(local_path)[1]
        blob_name = f"{prefix}/{uuid.uuid4()}{ext}"
        detected = content_type or mimetypes.guess_type(local_path)[0] or "application/octet-stream"

        blob = self.bucket.blob(blob_name)
        blob.upload_from_filename(local_path, content_type=detected)

        try:
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=settings.gcs_signed_url_ttl_seconds),
                method="GET",
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to generate signed URL. Ensure Cloud Run service account can sign blobs "
                "(roles/iam.serviceAccountTokenCreator) and has storage object access."
            ) from exc

        return UploadedMedia(
            gcs_uri=f"gs://{settings.gcs_media_bucket}/{blob_name}",
            signed_url=signed_url,
            content_type=detected,
            blob_name=blob_name,
        )
