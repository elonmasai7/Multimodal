from celery import Celery

celery = Celery(
    "modal_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

celery.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])


@celery.task(name="tasks.generate_media")
def generate_media(payload: dict) -> dict:
    return {
        "status": "queued_complete",
        "outputs": {
            "text": "Generated lesson narrative",
            "image": "gs://bucket/generated-diagram.png",
            "video": "gs://bucket/generated-video.mp4",
            "audio": "gs://bucket/generated-audio.mp3",
        },
        "payload": payload,
    }
