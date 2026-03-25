from __future__ import annotations

from celery import Task

from backend.celery_app import celery_app
from backend.db.models import Detection, Job
from backend.db.session import session_scope
from backend.pipeline.zone1.ocr import analyze_ocr

from backend.tasks.task_ingest import RetryableTask


@celery_app.task(bind=True, base=RetryableTask, name="task_ocr")
def task_ocr(self: Task, job_id: str) -> str:
    with session_scope() as db:
        job = db.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        try:
            payload = analyze_ocr(job_id, job.frames_dir or "")
            detection = job.detection or Detection(job_id=job.id)
            detection.ocr_results = payload["ocr_results"]
            job.status = "ocr_complete"
            db.add(detection)
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            raise
    return job_id
