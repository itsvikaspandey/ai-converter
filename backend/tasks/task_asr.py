from __future__ import annotations

from celery import Task

from backend.celery_app import celery_app
from backend.db.models import Job, Transcript
from backend.db.session import session_scope
from backend.pipeline.zone1.asr import transcribe_job

from backend.tasks.task_ingest import RetryableTask


@celery_app.task(bind=True, base=RetryableTask, name="task_asr")
def task_asr(self: Task, job_id: str) -> str:
    with session_scope() as db:
        job = db.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        try:
            payload = transcribe_job(job_id, job.audio_path or "")
            transcript = job.transcript or Transcript(job_id=job.id)
            transcript.words = payload["words"]
            transcript.segments = payload["segments"]
            job.language = payload["language"]
            job.status = "transcribed"
            db.add(transcript)
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            raise
    return job_id
