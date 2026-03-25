from __future__ import annotations

PROGRESS_BY_STATUS = {
    "pending": 0,
    "ingested": 10,
    "transcribed": 25,
    "vision_complete": 40,
    "ocr_complete": 50,
    "audio_analyzed": 60,
    "scoring_complete": 70,
    "crop_planned": 80,
    "aligned": 90,
    "complete": 100,
    "failed": 100,
}

STEP_LABELS = {
    "pending": "Queued",
    "ingested": "Media ingested",
    "transcribed": "Transcript ready",
    "vision_complete": "Vision analysis ready",
    "ocr_complete": "OCR ready",
    "audio_analyzed": "Audio energy analyzed",
    "scoring_complete": "Candidate clips scored",
    "crop_planned": "Crop trajectories planned",
    "aligned": "Trajectories aligned",
    "complete": "Rendering complete",
    "failed": "Failed",
}


def progress_for_status(status: str) -> int:
    return PROGRESS_BY_STATUS.get(status, 0)


def step_label(status: str) -> str:
    return STEP_LABELS.get(status, status.replace("_", " ").title())
