from __future__ import annotations

from typing import Any

import requests


class APIClient:
    def __init__(self, base_url: str = "http://backend:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def create_job_from_file(self, file_name: str, file_bytes: bytes, preferred_framing_mode: str) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/jobs/create",
            files={"file": (file_name, file_bytes)},
            data={"preferred_framing_mode": preferred_framing_mode},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()

    def create_job_from_url(self, url: str, preferred_framing_mode: str) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/jobs/create",
            json={"url": url, "preferred_framing_mode": preferred_framing_mode},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/api/jobs/{job_id}/status", timeout=30)
        response.raise_for_status()
        return response.json()

    def get_job_clips(self, job_id: str) -> list[dict[str, Any]]:
        response = requests.get(f"{self.base_url}/api/jobs/{job_id}/clips", timeout=30)
        response.raise_for_status()
        return response.json()

    def get_transcript(self, job_id: str) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/api/jobs/{job_id}/transcript", timeout=30)
        response.raise_for_status()
        return response.json()

    def export_clip(self, clip_id: str) -> dict[str, Any]:
        response = requests.post(f"{self.base_url}/api/clips/{clip_id}/export", timeout=120)
        response.raise_for_status()
        return response.json()

    def override_clip(self, clip_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.patch(f"{self.base_url}/api/clips/{clip_id}/override", json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
