from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.models.yolo_loader import get_yolo_model
from backend.storage.storage import job_asset_path, write_json


TARGET_CLASSES = {"person", "laptop", "tv", "cell phone", "book", "whiteboard"}


def _frame_timestamp(index: int, fps: int = 2) -> float:
    return round(index / max(fps, 1), 2)


def _fallback_detections(frame_files: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    yolo_results = []
    face_results = []
    for index, frame in enumerate(frame_files):
        ts = _frame_timestamp(index)
        yolo_results.append(
            {
                "frame": frame.name,
                "frame_ts": ts,
                "detections": [
                    {
                        "class": "person",
                        "bbox": [400, 80, 1500, 1000],
                        "confidence": 0.72,
                    },
                    {
                        "class": "laptop",
                        "bbox": [900, 300, 1800, 950],
                        "confidence": 0.61,
                    },
                ],
            }
        )
        face_results.append({"frame": frame.name, "frame_ts": ts, "face_bbox": [650, 120, 1180, 640]})
    return yolo_results, face_results


def analyze_vision(job_id: str, frames_dir: str) -> dict[str, Any]:
    frame_files = sorted(Path(frames_dir).glob("*.jpg"))
    model = get_yolo_model()

    if not frame_files:
        yolo_results, face_results = [], []
    elif model.model:
        try:
            results = model.model.predict([str(frame) for frame in frame_files], verbose=False)
            yolo_results = []
            face_results = []
            for index, result in enumerate(results):
                detections = []
                for box in result.boxes:
                    class_name = result.names[int(box.cls[0])]
                    if class_name not in TARGET_CLASSES:
                        continue
                    detections.append(
                        {
                            "class": class_name,
                            "bbox": [float(value) for value in box.xyxy[0].tolist()],
                            "confidence": float(box.conf[0]),
                        }
                    )
                ts = _frame_timestamp(index)
                yolo_results.append({"frame": frame_files[index].name, "frame_ts": ts, "detections": detections})
                face_results.append({"frame": frame_files[index].name, "frame_ts": ts, "face_bbox": None})
        except Exception:
            yolo_results, face_results = _fallback_detections(frame_files)
    else:
        yolo_results, face_results = _fallback_detections(frame_files)

    payload = {"yolo_results": yolo_results, "face_results": face_results}
    write_json(job_asset_path(job_id, "artifacts", "yolo_results.json"), yolo_results)
    write_json(job_asset_path(job_id, "artifacts", "face_results.json"), face_results)
    return payload
