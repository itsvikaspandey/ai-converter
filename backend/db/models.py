from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.db.session import Base


def json_type():
    return JSONB().with_variant(JSON(), "sqlite")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(64), default="pending", nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_path: Mapped[str | None] = mapped_column(Text)
    audio_path: Mapped[str | None] = mapped_column(Text)
    frames_dir: Mapped[str | None] = mapped_column(Text)
    video_duration: Mapped[float | None] = mapped_column(Float)
    video_fps: Mapped[float | None] = mapped_column(Float)
    video_width: Mapped[int | None] = mapped_column(Integer)
    video_height: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str | None] = mapped_column(String(16))
    error_message: Mapped[str | None] = mapped_column(Text)

    transcript: Mapped["Transcript | None"] = relationship(back_populates="job", cascade="all, delete-orphan", uselist=False)
    detection: Mapped["Detection | None"] = relationship(back_populates="job", cascade="all, delete-orphan", uselist=False)
    clips: Mapped[list["Clip"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, unique=True)
    words: Mapped[list[dict]] = mapped_column(json_type(), default=list, nullable=False)
    segments: Mapped[list[dict]] = mapped_column(json_type(), default=list, nullable=False)
    audio_energy: Mapped[list[dict]] = mapped_column(json_type(), default=list, nullable=False)

    job: Mapped[Job] = relationship(back_populates="transcript")


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, unique=True)
    yolo_results: Mapped[list[dict]] = mapped_column(json_type(), default=list, nullable=False)
    face_results: Mapped[list[dict]] = mapped_column(json_type(), default=list, nullable=False)
    ocr_results: Mapped[list[dict]] = mapped_column(json_type(), default=list, nullable=False)

    job: Mapped[Job] = relationship(back_populates="detection")


class Clip(Base, TimestampMixin):
    __tablename__ = "clips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    framing_mode: Mapped[str] = mapped_column(String(32), default="mixed", nullable=False)
    transcript_snippet: Mapped[str] = mapped_column(Text, default="", nullable=False)
    crop_trajectory: Mapped[list[dict]] = mapped_column(json_type(), default=list, nullable=False)
    aligned_trajectory: Mapped[list[dict]] = mapped_column(json_type(), default=list, nullable=False)
    preview_path: Mapped[str | None] = mapped_column(Text)
    export_path: Mapped[str | None] = mapped_column(Text)

    job: Mapped[Job] = relationship(back_populates="clips")
