from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from backend.config import get_settings


settings = get_settings()


def ensure_dir(path: str | Path) -> Path:
    folder = Path(path)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def job_dir(job_id: str) -> Path:
    return ensure_dir(settings.storage_root / job_id)


def job_asset_path(job_id: str, kind: str, filename: str) -> Path:
    target = ensure_dir(job_dir(job_id) / kind)
    return target / filename


def save_upload(upload: UploadFile, target: Path) -> Path:
    ensure_dir(target.parent)
    with target.open("wb") as file_obj:
        shutil.copyfileobj(upload.file, file_obj)
    return target


def write_json(path: str | Path, payload: Any) -> Path:
    output = Path(path)
    ensure_dir(output.parent)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output


def read_json(path: str | Path, default: Any | None = None) -> Any:
    target = Path(path)
    if not target.exists():
        return default
    return json.loads(target.read_text(encoding="utf-8"))


def safe_relative_url(path: str | None) -> str | None:
    if not path:
        return None
    return Path(path).as_posix()
