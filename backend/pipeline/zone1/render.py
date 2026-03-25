from __future__ import annotations

import subprocess
import shutil
from pathlib import Path
from typing import Any

from backend.config import get_settings
from backend.storage.storage import ensure_dir, job_asset_path


settings = get_settings()


def _run_ffmpeg(command: list[str]) -> bool:
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except Exception:
        return False


def _placeholder_video(output_path: Path, source_path: str) -> None:
    source = Path(source_path)
    if source.exists():
        shutil.copy2(source, output_path)
    else:
        output_path.write_bytes(b"")


def render_clip_assets(
    job_id: str,
    clip_id: str,
    video_path: str,
    start: float,
    end: float,
    trajectory: list[dict[str, Any]],
) -> dict[str, str]:
    duration = max(end - start, 1.0)
    output_dir = ensure_dir(job_asset_path(job_id, "outputs", clip_id).parent)
    export_path = output_dir / f"{clip_id}_export.mp4"
    preview_path = output_dir / f"{clip_id}_preview.mp4"

    preview_ok = _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-i",
            str(video_path),
            "-vf",
            (
                f"scale={settings.preview_width}:{settings.preview_height}:force_original_aspect_ratio=decrease,"
                f"pad={settings.preview_width}:{settings.preview_height}:(ow-iw)/2:(oh-ih)/2:black,"
                "drawtext=text='PREVIEW':fontcolor=white@0.45:fontsize=56:x=(w-text_w)/2:y=(h-text_h)/2:rotate=0.35"
            ),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-c:a",
            "aac",
            str(preview_path),
        ]
    )
    export_ok = _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-i",
            str(video_path),
            "-vf",
            f"scale={settings.export_width}:{settings.export_height}:force_original_aspect_ratio=decrease,pad={settings.export_width}:{settings.export_height}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-c:a",
            "aac",
            str(export_path),
        ]
    )

    if not preview_ok:
        _placeholder_video(preview_path, video_path)
    if not export_ok:
        _placeholder_video(export_path, video_path)

    return {
        "preview_path": str(preview_path),
        "export_path": str(export_path),
    }
