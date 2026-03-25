from __future__ import annotations

from uuid import uuid4

from celery import Task

from backend.pipeline.zone2.agents.alignment_agent import run_alignment_agent
from backend.pipeline.zone2.agents.crop_planner_agent import run_crop_planner_agent
from backend.pipeline.zone2.agents.scoring_agent import run_scoring_agent
from backend.celery_app import celery_app
from backend.db.models import Clip, Job
from backend.db.session import session_scope
from backend.pipeline.zone2.state import VideoJobState

from backend.tasks.task_ingest import RetryableTask


@celery_app.task(bind=True, base=RetryableTask, name="task_langgraph_zone2")
def task_langgraph_zone2(self: Task, job_id: str) -> str:
    with session_scope() as db:
        job = db.get(Job, job_id)
        if job is None or job.transcript is None or job.detection is None:
            raise ValueError(f"Job graph dependencies missing: {job_id}")
        try:
            state: VideoJobState = {
                "job_id": job_id,
                "transcript": job.transcript.words,
                "segments": job.transcript.segments,
                "detections": job.detection.yolo_results,
                "face_results": job.detection.face_results,
                "ocr_regions": job.detection.ocr_results,
                "audio_energy": job.transcript.audio_energy,
                "candidate_clips": [],
                "crop_trajectories": [],
                "aligned_trajectories": [],
                "errors": [],
                "current_step": "audio_analyzed",
            }
            state = run_scoring_agent(state)
            job.status = "scoring_complete"
            db.commit()

            state = run_crop_planner_agent(state)
            job.status = "crop_planned"
            db.commit()

            result = run_alignment_agent(state)
            job.status = "aligned"
            db.commit()

            existing_clips = list(job.clips)
            for clip in existing_clips:
                db.delete(clip)
            db.flush()

            crop_lookup = {item["clip_index"]: item for item in result.get("crop_trajectories", [])}
            aligned_lookup = {item["clip_index"]: item for item in result.get("aligned_trajectories", [])}
            for index, candidate in enumerate(result.get("candidate_clips", [])):
                crop = crop_lookup.get(index, {})
                aligned = aligned_lookup.get(index, {})
                db.add(
                    Clip(
                        id=uuid4(),
                        job_id=job.id,
                        start_time=float(candidate["start"]),
                        end_time=float(candidate["end"]),
                        score=float(candidate["score"]),
                        reason=candidate["reason"],
                        framing_mode=crop.get("framing_mode", "mixed"),
                        transcript_snippet=candidate["transcript_snippet"],
                        crop_trajectory=crop.get("frames", []),
                        aligned_trajectory=aligned.get("frames", crop.get("frames", [])),
                    )
                )
            job.status = "aligned"
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            raise
    return job_id
