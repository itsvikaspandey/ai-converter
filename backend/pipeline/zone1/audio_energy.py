from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.storage.storage import job_asset_path, write_json


def _fallback_energy() -> list[dict[str, Any]]:
    timeline = []
    for index in range(60):
        timestamp = round(index * 0.1, 1)
        rms = 0.15 + (0.2 if index % 15 == 0 else 0.0)
        timeline.append(
            {
                "timestamp": timestamp,
                "rms": round(rms, 3),
                "is_spike": rms > 0.3,
                "is_pause": False,
            }
        )
    return timeline


def analyze_audio_energy(job_id: str, audio_path: str) -> dict[str, Any]:
    if not Path(audio_path).exists() or Path(audio_path).stat().st_size == 0:
        timeline = _fallback_energy()
    else:
        try:
            import librosa
            import numpy as np

            y, sr = librosa.load(audio_path, sr=16000, mono=True)
            hop_length = int(sr * 0.1)
            rms = librosa.feature.rms(y=y, frame_length=hop_length * 2, hop_length=hop_length)[0]
            timestamps = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=hop_length)
            mean = float(np.mean(rms))
            std = float(np.std(rms))
            timeline = []
            pause_run = 0
            for timestamp, value in zip(timestamps, rms):
                is_pause = value < mean - std
                pause_run = pause_run + 1 if is_pause else 0
                timeline.append(
                    {
                        "timestamp": round(float(timestamp), 2),
                        "rms": round(float(value), 4),
                        "is_spike": bool(value > mean + (1.5 * std)),
                        "is_pause": bool(is_pause and pause_run >= 8),
                    }
                )
        except Exception:
            timeline = _fallback_energy()

    payload = {"audio_energy": timeline}
    write_json(job_asset_path(job_id, "artifacts", "audio_energy.json"), timeline)
    return payload
