from __future__ import annotations

from celery import Task

from backend.celery_app import celery_app
from backend.db.models import Clip
from backend.db.session import session_scope
from backend.pipeline.zone1.render import render_clip_assets

from backend.tasks.task_ingest import RetryableTask


@celery_app.task(bind=True, base=RetryableTask, name="task_clip_override")
def task_clip_override(self: Task, clip_id: str) -> str:
    with session_scope() as db:
        clip = db.get(Clip, clip_id)
        if clip is None:
            raise ValueError(f"Clip not found: {clip_id}")
        job = clip.job
        rendered = render_clip_assets(
            job_id=str(job.id),
            clip_id=str(clip.id),
            video_path=job.source_path or "",
            start=clip.start_time,
            end=clip.end_time,
            trajectory=clip.aligned_trajectory,
        )
        clip.preview_path = rendered["preview_path"]
        clip.export_path = rendered["export_path"]
    return clip_id
