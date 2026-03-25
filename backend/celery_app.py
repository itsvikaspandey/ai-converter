from __future__ import annotations

import logging
from urllib.parse import urlparse

import requests
from celery import Celery
from celery.signals import worker_ready

from backend.config import get_settings
from backend.models.ocr_loader import get_ocr_model
from backend.models.whisper_loader import get_whisper_model
from backend.models.yolo_loader import get_yolo_model


settings = get_settings()
celery_app = Celery("ai_converter", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_track_started=True,
    task_always_eager=settings.celery_eager,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

logger = logging.getLogger(__name__)


@worker_ready.connect
def warm_models(**_: object) -> None:
    get_whisper_model()
    get_yolo_model()
    get_ocr_model()
    try:
        requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5).raise_for_status()
        logger.info("All models loaded. Worker ready.")
    except Exception as exc:
        logger.warning("Models loaded but Ollama check failed: %s", exc)
