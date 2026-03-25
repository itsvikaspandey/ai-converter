from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from backend.config import get_settings
from backend.storage.storage import ensure_dir, job_asset_path, write_json


settings = get_settings()


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True, capture_output=True, text=True)


def _ffprobe(video_path: Path) -> dict[str, Any]:
    try:
        output = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        data = json.loads(output.stdout)
        video_stream = next((stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"), {})
        duration = float(data.get("format", {}).get("duration", 0.0))
        r_frame_rate = video_stream.get("r_frame_rate", "0/1")
        num, den = r_frame_rate.split("/")
        fps = float(num) / max(float(den), 1.0)
        return {
            "duration": duration,
            "fps": fps,
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "codec": video_stream.get("codec_name", "unknown"),
        }
    except Exception:
        return {
            "duration": 0.0,
            "fps": 0.0,
            "width": 1920,
            "height": 1080,
            "codec": "unknown",
        }


def _download_from_url(url: str, job_id: str) -> Path:
    output_path = job_asset_path(job_id, "source", "source.mp4")
    ensure_dir(output_path.parent)
    try:
        _run(["yt-dlp", "-o", str(output_path), url])
        return output_path
    except Exception as exc:
        raise RuntimeError(f"Failed to download URL with yt-dlp: {exc}") from exc


def _extract_audio(video_path: Path, job_id: str) -> Path:
    audio_path = job_asset_path(job_id, "audio", "audio.wav")
    try:
        _run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-ac",
                "1",
                "-ar",
                "16000",
                str(audio_path),
            ]
        )
    except Exception:
        audio_path.write_bytes(b"")
    return audio_path


def _extract_frames(video_path: Path, job_id: str) -> Path:
    frames_dir = job_asset_path(job_id, "frames", "frame_%06d.jpg").parent
    ensure_dir(frames_dir)
    try:
        _run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"fps={settings.frame_extract_fps}",
                str(frames_dir / "frame_%06d.jpg"),
            ]
        )
    except Exception:
        # Leave the directory empty so later stages can still proceed with fallbacks.
        pass
    return frames_dir


def ingest_job(job_id: str, source_type: str, source_path: str) -> dict[str, Any]:
    source = Path(source_path)
    if source_type == "url":
        video_path = _download_from_url(source_path, job_id)
    else:
        video_path = job_asset_path(job_id, "source", source.name)
        ensure_dir(video_path.parent)
        if source.resolve() != video_path.resolve():
            shutil.copy2(source, video_path)

    metadata = _ffprobe(video_path)
    audio_path = _extract_audio(video_path, job_id)
    frames_dir = _extract_frames(video_path, job_id)
    manifest = {
        "video_path": str(video_path),
        "audio_path": str(audio_path),
        "frames_dir": str(frames_dir),
        "metadata": metadata,
    }
    write_json(job_asset_path(job_id, "artifacts", "ingest.json"), manifest)
    return manifest
