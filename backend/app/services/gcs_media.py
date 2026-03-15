import mimetypes
import os
import uuid
from dataclasses import dataclass
from datetime import timedelta

import google.auth
import google.auth.transport.requests
from google.cloud import storage

from app.core.config import settings
from app.core.errors import StorageError
from app.core.retry import retry_sync


@dataclass
class UploadedMedia:
    gcs_uri: str
    signed_url: str
    content_type: str
    blob_name: str


class GCSMediaService:
    def __init__(self) -> None:
        if not settings.gcs_media_bucket:
            raise StorageError("GCS_MEDIA_BUCKET is required for media uploads", retryable=False)
        self._credentials, _ = google.auth.default()
        self.client = storage.Client(project=settings.gcp_project_id or None, credentials=self._credentials)
        self.bucket = self.client.bucket(settings.gcs_media_bucket)

    def _refresh_credentials(self) -> tuple[str, str]:
        """Refresh ADC credentials and return (service_account_email, access_token).

        On Cloud Run, generate_signed_url(version='v4') requires passing the
        service account email and a fresh access token so the GCS library can
        call IAM signBlob on our behalf instead of attempting a local sign.
        """
        request = google.auth.transport.requests.Request()
        self._credentials.refresh(request)
        sa_email = getattr(self._credentials, "service_account_email", None)
        token = getattr(self._credentials, "token", None)
        return sa_email, token

    def _generate_signed_url(self, blob: storage.Blob) -> str:
        sa_email, token = self._refresh_credentials()
        kwargs: dict = {
            "version": "v4",
            "expiration": timedelta(seconds=settings.gcs_signed_url_ttl_seconds),
            "method": "GET",
        }
        if sa_email and token:
            kwargs["service_account_email"] = sa_email
            kwargs["access_token"] = token
        return blob.generate_signed_url(**kwargs)

    def sign_gcs_uri(self, gcs_uri: str) -> str:
        """Generate a signed URL for an existing GCS object given its gs:// URI."""
        # gs://bucket/path/to/blob  ->  bucket, path/to/blob
        without_scheme = gcs_uri[len("gs://"):]
        bucket_name, _, blob_name = without_scheme.partition("/")
        blob = self.client.bucket(bucket_name).blob(blob_name)
        return self._generate_signed_url(blob)

    def upload_bytes_and_sign(self, *, data: bytes, prefix: str, content_type: str = "image/png") -> UploadedMedia:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".bin"
        # Some MIME types map to unexpected extensions; normalise common cases
        if content_type.startswith("image/png"):
            ext = ".png"
        elif content_type.startswith("image/jpeg"):
            ext = ".jpg"
        elif content_type.startswith("image/webp"):
            ext = ".webp"
        blob_name = f"{prefix}/{uuid.uuid4()}{ext}"
        blob = self.bucket.blob(blob_name)
        try:
            retry_sync(
                lambda: blob.upload_from_string(data, content_type=content_type),
                attempts=settings.retry_max_attempts,
                base_delay=settings.retry_base_delay_seconds,
                max_delay=settings.retry_max_delay_seconds,
                stage="storage",
                retry_on=(Exception,),
            )
        except Exception as exc:
            raise StorageError(f"Failed to upload bytes: {exc}") from exc

        try:
            signed_url = retry_sync(
                lambda: self._generate_signed_url(blob),
                attempts=settings.retry_max_attempts,
                base_delay=settings.retry_base_delay_seconds,
                max_delay=settings.retry_max_delay_seconds,
                stage="storage",
                retry_on=(Exception,),
            )
        except Exception as exc:
            try:
                blob.delete()
            except Exception:
                pass
            raise StorageError("Failed to generate signed URL for inline image") from exc

        return UploadedMedia(
            gcs_uri=f"gs://{settings.gcs_media_bucket}/{blob_name}",
            signed_url=signed_url,
            content_type=content_type,
            blob_name=blob_name,
        )

    def upload_file_and_sign(self, *, local_path: str, prefix: str, content_type: str | None = None) -> UploadedMedia:
        ext = os.path.splitext(local_path)[1]
        blob_name = f"{prefix}/{uuid.uuid4()}{ext}"
        detected = content_type or mimetypes.guess_type(local_path)[0] or "application/octet-stream"

        blob = self.bucket.blob(blob_name)
        try:
            retry_sync(
                lambda: blob.upload_from_filename(local_path, content_type=detected),
                attempts=settings.retry_max_attempts,
                base_delay=settings.retry_base_delay_seconds,
                max_delay=settings.retry_max_delay_seconds,
                stage="storage",
                retry_on=(Exception,),
            )
        except Exception as exc:
            raise StorageError(f"Failed to upload media: {exc}") from exc

        try:
            signed_url = retry_sync(
                lambda: self._generate_signed_url(blob),
                attempts=settings.retry_max_attempts,
                base_delay=settings.retry_base_delay_seconds,
                max_delay=settings.retry_max_delay_seconds,
                stage="storage",
                retry_on=(Exception,),
            )
        except Exception as exc:
            try:
                blob.delete()
            except Exception:
                pass
            raise StorageError(
                "Failed to generate signed URL. Ensure Cloud Run service account can sign blobs "
                "(roles/iam.serviceAccountTokenCreator) and has storage object access."
            ) from exc

        return UploadedMedia(
            gcs_uri=f"gs://{settings.gcs_media_bucket}/{blob_name}",
            signed_url=signed_url,
            content_type=detected,
            blob_name=blob_name,
        )
