from __future__ import annotations

import logging
from functools import lru_cache

from backend.config import get_settings

logger = logging.getLogger(__name__)


class OCRModelWrapper:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = None
        self.backend = "fallback"
        self._load()

    def _load(self) -> None:
        try:
            from paddleocr import PaddleOCR

            self.model = PaddleOCR(use_angle_cls=False, lang="en", use_gpu=self.settings.enable_gpu)
            self.backend = "paddleocr"
            logger.info("Loaded PaddleOCR model")
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning("Falling back to mock OCR: %s", exc)


@lru_cache(maxsize=1)
def get_ocr_model() -> OCRModelWrapper:
    return OCRModelWrapper()
