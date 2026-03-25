from __future__ import annotations

from celery import Task

from backend.celery_app import celery_app
from backend.db.models import Job
from backend.db.session import session_scope
from backend.pipeline.zone1.ingest import ingest_job


class RetryableTask(Task):
    autoretry_for = (Exception,)
    max_retries = 2
    retry_backoff = 10
    retry_jitter = False


@celery_app.task(bind=True, base=RetryableTask, name="task_ingest")
def task_ingest(self: Task, job_id: str) -> str:
    with session_scope() as db:
        job = db.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        try:
            result = ingest_job(job_id, job.source_type, job.source_path or "")
            metadata = result["metadata"]
            job.source_path = result["video_path"]
            job.audio_path = result["audio_path"]
            job.frames_dir = result["frames_dir"]
            job.video_duration = metadata["duration"]
            job.video_fps = metadata["fps"]
            job.video_width = metadata["width"]
            job.video_height = metadata["height"]
            job.status = "ingested"
            job.error_message = None
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            raise
    return job_id
