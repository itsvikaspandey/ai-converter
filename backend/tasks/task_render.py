from __future__ import annotations

from celery import Task

from backend.celery_app import celery_app
from backend.db.models import Job
from backend.db.session import session_scope
from backend.pipeline.zone1.render import render_clip_assets

from backend.tasks.task_ingest import RetryableTask


@celery_app.task(bind=True, base=RetryableTask, name="task_render")
def task_render(self: Task, job_id: str) -> str:
    with session_scope() as db:
        job = db.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        try:
            for clip in job.clips:
                rendered = render_clip_assets(
                    job_id=job_id,
                    clip_id=str(clip.id),
                    video_path=job.source_path or "",
                    start=clip.start_time,
                    end=clip.end_time,
                    trajectory=clip.aligned_trajectory,
                )
                clip.preview_path = rendered["preview_path"]
                clip.export_path = rendered["export_path"]
            job.status = "complete"
            job.error_message = None
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            raise
    return job_id
