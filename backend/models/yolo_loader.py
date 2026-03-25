from __future__ import annotations

import logging
from functools import lru_cache

from backend.config import get_settings

logger = logging.getLogger(__name__)


class YOLOModelWrapper:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = None
        self.backend = "fallback"
        self._load()

    def _load(self) -> None:
        try:
            from ultralytics import YOLO

            self.model = YOLO(self.settings.yolo_model)
            self.backend = "ultralytics"
            logger.info("Loaded YOLO model %s", self.settings.yolo_model)
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning("Falling back to mock vision detection: %s", exc)


@lru_cache(maxsize=1)
def get_yolo_model() -> YOLOModelWrapper:
    return YOLOModelWrapper()
