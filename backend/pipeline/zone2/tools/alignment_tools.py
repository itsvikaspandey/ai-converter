from __future__ import annotations

from typing import Any

from backend.pipeline.zone2.tools.crop_tools import exponential_moving_average


VISUAL_REFERENCE_PHRASES = [
    "look at this",
    "here's the",
    "on the right",
    "on the left",
    "this graph",
    "this chart",
    "this code",
    "as you can see",
    "over here",
    "right here",
]


def find_visual_reference_timestamps(words: list[dict[str, Any]]) -> list[float]:
    text = " ".join(item.get("word", "") for item in words).lower()
    results = []
    for phrase in VISUAL_REFERENCE_PHRASES:
        offset = text.find(phrase)
        if offset == -1:
            continue
        running = 0
        for word in words:
            running += len(word.get("word", "")) + 1
            if running >= offset:
                results.append(float(word.get("start", 0.0)))
                break
    return results


def smooth_trajectory(frames: list[dict[str, Any]], alpha: float = 0.15) -> list[dict[str, Any]]:
    if not frames:
        return frames
    xs = exponential_moving_average([float(frame["cx"]) for frame in frames], alpha=alpha)
    ys = exponential_moving_average([float(frame["cy"]) for frame in frames], alpha=alpha)
    scales = exponential_moving_average([float(frame["scale"]) for frame in frames], alpha=alpha)
    updated = []
    for frame, x, y, scale in zip(frames, xs, ys, scales):
        current = dict(frame)
        current["cx"] = round(x, 2)
        current["cy"] = round(y, 2)
        current["scale"] = round(scale, 4)
        updated.append(current)
    return updated
