from __future__ import annotations

from celery import Task

from backend.celery_app import celery_app
from backend.db.models import Job, Transcript
from backend.db.session import session_scope
from backend.pipeline.zone1.audio_energy import analyze_audio_energy

from backend.tasks.task_ingest import RetryableTask


@celery_app.task(bind=True, base=RetryableTask, name="task_audio_energy")
def task_audio_energy(self: Task, job_id: str) -> str:
    with session_scope() as db:
        job = db.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        try:
            payload = analyze_audio_energy(job_id, job.audio_path or "")
            transcript = job.transcript or Transcript(job_id=job.id)
            transcript.audio_energy = payload["audio_energy"]
            job.status = "audio_analyzed"
            db.add(transcript)
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            raise
    return job_id
