from __future__ import annotations

from collections import Counter
from typing import Any


def exponential_moving_average(values: list[float], alpha: float = 0.15) -> list[float]:
    if not values:
        return []
    smoothed = [values[0]]
    for value in values[1:]:
        smoothed.append((alpha * value) + ((1 - alpha) * smoothed[-1]))
    return smoothed


def clip_frames_for_timerange(
    detections: list[dict[str, Any]],
    faces: list[dict[str, Any]],
    ocr_regions: list[dict[str, Any]],
    start: float,
    end: float,
) -> list[dict[str, Any]]:
    face_lookup = {round(item["frame_ts"], 2): item.get("face_bbox") for item in faces}
    ocr_lookup = {round(item["frame_ts"], 2): item.get("regions", []) for item in ocr_regions}
    frames = []
    for frame in detections:
        ts = round(frame.get("frame_ts", 0.0), 2)
        if not (start <= ts <= end):
            continue
        frames.append(
            {
                "ts": ts,
                "detections": frame.get("detections", []),
                "face_bbox": face_lookup.get(ts),
                "ocr_regions": ocr_lookup.get(ts, []),
            }
        )
    return frames


def choose_focus_region(frame: dict[str, Any], frame_width: int, frame_height: int) -> tuple[dict[str, Any], str]:
    regions: list[tuple[int, dict[str, Any], str]] = []
    for region in frame.get("ocr_regions", []):
        if region.get("is_code_block"):
            regions.append((5, region, "content"))
        else:
            regions.append((4, region, "content"))
    for detection in frame.get("detections", []):
        kind = detection.get("class")
        if kind in {"laptop", "tv"}:
            regions.append((4, detection, "content"))
        elif kind == "person":
            regions.append((1, detection, "speaker"))
    if frame.get("face_bbox"):
        regions.append((3, {"bbox": frame["face_bbox"]}, "speaker"))
    if not regions:
        return {"bbox": [0, 0, frame_width, frame_height]}, "mixed"
    regions.sort(key=lambda item: item[0], reverse=True)
    return regions[0][1], regions[0][2]


def bbox_center(bbox: list[float]) -> tuple[float, float]:
    return (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0


def dominant_mode(modes: list[str]) -> str:
    if not modes:
        return "mixed"
    counts = Counter(modes)
    total = len(modes)
    if counts.get("speaker", 0) / total > 0.6:
        return "speaker"
    if counts.get("content", 0) / total > 0.6:
        return "content"
    return "mixed"
