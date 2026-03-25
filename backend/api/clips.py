from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.db.models import Clip
from backend.db.session import get_db
from backend.schemas import ClipOverrideRequest
from backend.tasks.task_clip_override import task_clip_override


router = APIRouter(prefix="/clips", tags=["clips"])
settings = get_settings()


@router.get("/{clip_id}/preview")
def stream_preview(clip_id: str, db: Session = Depends(get_db)) -> FileResponse:
    clip = db.get(Clip, clip_id)
    if clip is None or not clip.preview_path:
        raise HTTPException(status_code=404, detail="Preview not found")
    preview_path = Path(clip.preview_path)
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail="Preview file missing")
    return FileResponse(preview_path, media_type="video/mp4", filename=preview_path.name)


@router.post("/{clip_id}/export")
def export_clip(clip_id: str, db: Session = Depends(get_db)) -> dict[str, str | None]:
    clip = db.get(Clip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    export_url = None
    if clip.export_path:
        export_rel = Path(clip.export_path).resolve().relative_to(settings.storage_root)
        export_url = f"/storage/{export_rel.as_posix()}"
    return {"export_url": export_url}


@router.patch("/{clip_id}/override")
def override_clip(clip_id: str, payload: ClipOverrideRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    clip = db.get(Clip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    if payload.framing_mode != "auto":
        clip.framing_mode = payload.framing_mode
    if payload.start_time is not None:
        clip.start_time = payload.start_time
    if payload.end_time is not None:
        clip.end_time = payload.end_time
    if payload.crop_overrides:
        overrides = {round(item.ts, 2): item for item in payload.crop_overrides}
        updated = []
        for frame in clip.aligned_trajectory:
            ts = round(frame.get("ts", 0.0), 2)
            if ts in overrides:
                override = overrides[ts]
                current = dict(frame)
                current["cx"] = override.cx
                current["cy"] = override.cy
                updated.append(current)
            else:
                updated.append(frame)
        clip.aligned_trajectory = updated
    db.add(clip)
    db.commit()
    task_clip_override.delay(str(clip.id))
    return {"clip_id": str(clip.id), "status": "re-rendering"}
