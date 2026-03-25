from __future__ import annotations

from typing import Any, TypedDict


class VideoJobState(TypedDict, total=False):
    job_id: str
    transcript: list[dict[str, Any]]
    segments: list[dict[str, Any]]
    detections: list[dict[str, Any]]
    face_results: list[dict[str, Any]]
    ocr_regions: list[dict[str, Any]]
    audio_energy: list[dict[str, Any]]
    candidate_clips: list[dict[str, Any]]
    crop_trajectories: list[dict[str, Any]]
    aligned_trajectories: list[dict[str, Any]]
    errors: list[str]
    current_step: str
