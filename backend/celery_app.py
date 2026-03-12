from celery import Celery

from app.core.errors import AppError, ExternalServiceError
from app.core.validation import validate_prompt
from app.services.ai_orchestrator import engine

celery = Celery(
    "modal_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

celery.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])


@celery.task(name="tasks.generate_media")
def generate_media(payload: dict) -> dict:
    try:
        prompt = validate_prompt(str(payload.get("prompt", "")))
        session_type = str(payload.get("session_type", "lesson"))
        plan = engine.generate_lesson_plan(prompt=prompt, session_type=session_type)
        image = engine.generate_image(str(plan.get("image_prompt", prompt)))
        audio = engine.synthesize_audio(str(plan.get("narration", prompt)))

        return {
            "status": "ok",
            "plan": plan,
            "image": image,
            "audio": audio,
        }
    except AppError as exc:
        return exc.to_payload(request_id=str(payload.get("request_id") or ""))
    except Exception as exc:
        return ExternalServiceError(str(exc), stage="response", retryable=False).to_payload(
            request_id=str(payload.get("request_id") or "")
        )
