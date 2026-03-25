from __future__ import annotations

import logging
from functools import lru_cache

from backend.config import get_settings

logger = logging.getLogger(__name__)


class WhisperModelWrapper:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.pipeline = None
        self.backend = "fallback"
        self._load()

    def _load(self) -> None:
        try:
            from transformers import pipeline

            self.pipeline = pipeline(
                "automatic-speech-recognition",
                model=self.settings.whisper_model,
                device="cuda:0" if self.settings.enable_gpu else "cpu",
            )
            self.backend = "transformers"
            logger.info("Loaded Whisper model %s via transformers", self.settings.whisper_model)
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning("Falling back to mock ASR: %s", exc)


@lru_cache(maxsize=1)
def get_whisper_model() -> WhisperModelWrapper:
    return WhisperModelWrapper()
