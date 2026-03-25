from __future__ import annotations

from celery import Task

from backend.celery_app import celery_app
from backend.db.models import Detection, Job
from backend.db.session import session_scope
from backend.pipeline.zone1.vision import analyze_vision

from backend.tasks.task_ingest import RetryableTask


@celery_app.task(bind=True, base=RetryableTask, name="task_vision")
def task_vision(self: Task, job_id: str) -> str:
    with session_scope() as db:
        job = db.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        try:
            payload = analyze_vision(job_id, job.frames_dir or "")
            detection = job.detection or Detection(job_id=job.id)
            detection.yolo_results = payload["yolo_results"]
            detection.face_results = payload["face_results"]
            job.status = "vision_complete"
            db.add(detection)
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            raise
    return job_id
