from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Long-Form to Reels Converter"
    api_prefix: str = "/api"
    database_url: str = Field(default="postgresql+psycopg://postgres:postgres@postgres:5432/ai_converter")
    redis_url: str = Field(default="redis://redis:6379/0")
    storage_path: str = Field(default="./storage")
    ollama_base_url: str = Field(default="http://ollama:11434")
    whisper_model: str = Field(default="openai/whisper-large-v3")
    yolo_model: str = Field(default="yolov8n.pt")
    max_video_duration_mins: int = Field(default=60)
    max_clips_per_job: int = Field(default=10)
    frame_extract_fps: int = Field(default=2)
    preview_height: int = Field(default=1280)
    preview_width: int = Field(default=720)
    export_height: int = Field(default=1920)
    export_width: int = Field(default=1080)
    celery_eager: bool = Field(default=False)
    enable_gpu: bool = Field(default=False)
    worker_model_fallback: bool = Field(default=True)
    allowed_upload_extensions: tuple[str, ...] = ("mp4", "mov", "mkv")
    temp_dir_name: str = Field(default="tmp")

    @property
    def storage_root(self) -> Path:
        return Path(self.storage_path).resolve()

    @property
    def videos_dir(self) -> Path:
        return self.storage_root / "videos"

    @property
    def audio_dir(self) -> Path:
        return self.storage_root / "audio"

    @property
    def frames_dir(self) -> Path:
        return self.storage_root / "frames"

    @property
    def outputs_dir(self) -> Path:
        return self.storage_root / "outputs"

    @property
    def temp_dir(self) -> Path:
        return self.storage_root / self.temp_dir_name


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    for path in (
        settings.storage_root,
        settings.videos_dir,
        settings.audio_dir,
        settings.frames_dir,
        settings.outputs_dir,
        settings.temp_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
    return settings
