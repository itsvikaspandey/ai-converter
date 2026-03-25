from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class JobCreateURLRequest(BaseModel):
    url: HttpUrl
    preferred_framing_mode: str = "auto"


class JobCreateResponse(BaseModel):
    job_id: UUID
    status: str


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    progress_percent: int
    current_step: str
    estimated_seconds_remaining: int | None = None
    errors: list[str] = Field(default_factory=list)


class ClipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clip_id: UUID
    start: float
    end: float
    score: float
    reason: str
    framing_mode: str
    transcript_snippet: str
    preview_url: str | None = None
    export_url: str | None = None


class ClipOverridePoint(BaseModel):
    ts: float
    cx: float
    cy: float


class ClipOverrideRequest(BaseModel):
    framing_mode: Literal["auto", "speaker", "content", "mixed"] = "auto"
    crop_overrides: list[ClipOverridePoint] = Field(default_factory=list)
    start_time: float | None = None
    end_time: float | None = None
    transcript_text: str | None = None


class TranscriptResponse(BaseModel):
    job_id: UUID
    words: list[dict[str, Any]]
    segments: list[dict[str, Any]]
