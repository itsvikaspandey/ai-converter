from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from celery import chain
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from backend.db.models import Job
from backend.db.session import get_db
from backend.pipeline.status import progress_for_status, step_label
from backend.schemas import JobCreateResponse, JobStatusResponse, TranscriptResponse
from backend.storage.storage import ensure_dir, job_asset_path
from backend.tasks.task_asr import task_asr
from backend.tasks.task_audio_energy import task_audio_energy
from backend.tasks.task_ingest import task_ingest
from backend.tasks.task_langgraph_zone2 import task_langgraph_zone2
from backend.tasks.task_ocr import task_ocr
from backend.tasks.task_render import task_render
from backend.tasks.task_vision import task_vision


router = APIRouter(prefix="/jobs", tags=["jobs"])


def enqueue_job(job_id: str) -> None:
    workflow = chain(
        task_ingest.s(job_id),
        task_asr.s(),
        task_vision.s(),
        task_ocr.s(),
        task_audio_energy.s(),
        task_langgraph_zone2.s(),
        task_render.s(),
    )
    workflow.delay()


@router.post("/create", response_model=JobCreateResponse)
async def create_job(
    request: Request,
    file: UploadFile | None = File(default=None),
    preferred_framing_mode: str = Form(default="auto"),
    db: Session = Depends(get_db),
) -> JobCreateResponse:
    source_type = None
    source_path = None
    if file is not None:
        suffix = Path(file.filename or "upload.mp4").suffix or ".mp4"
        temp_path = job_asset_path(str(uuid.uuid4()), "incoming", f"upload{suffix}")
        ensure_dir(temp_path.parent)
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        source_type = "file"
        source_path = str(temp_path)
    else:
        payload = await request.json()
        url = payload.get("url")
        preferred_framing_mode = payload.get("preferred_framing_mode", preferred_framing_mode)
        if not url:
            raise HTTPException(status_code=400, detail="Provide either a file upload or a url")
        source_type = "url"
        source_path = url

    job = Job(status="pending", source_type=source_type, source_path=source_path)
    db.add(job)
    db.commit()
    db.refresh(job)
    enqueue_job(str(job.id))
    return JobCreateResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)) -> JobStatusResponse:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    estimated = max(0, int((100 - progress_for_status(job.status)) * 4))
    errors = [job.error_message] if job.error_message else []
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress_percent=progress_for_status(job.status),
        current_step=step_label(job.status),
        estimated_seconds_remaining=estimated,
        errors=errors,
    )


@router.get("/{job_id}/clips")
def list_job_clips(job_id: str, db: Session = Depends(get_db)) -> list[dict]:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return [
        {
            "clip_id": clip.id,
            "start": clip.start_time,
            "end": clip.end_time,
            "score": clip.score,
            "reason": clip.reason,
            "framing_mode": clip.framing_mode,
            "transcript_snippet": clip.transcript_snippet,
            "preview_url": f"/api/clips/{clip.id}/preview",
            "export_url": f"/api/clips/{clip.id}/export",
        }
        for clip in job.clips
    ]


@router.get("/{job_id}/transcript", response_model=TranscriptResponse)
def get_job_transcript(job_id: str, db: Session = Depends(get_db)) -> TranscriptResponse:
    job = db.get(Job, job_id)
    if job is None or job.transcript is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return TranscriptResponse(job_id=job.id, words=job.transcript.words, segments=job.transcript.segments)
