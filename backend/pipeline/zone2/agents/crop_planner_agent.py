from __future__ import annotations

from typing import Any

from backend.pipeline.zone2.state import VideoJobState
from backend.pipeline.zone2.tools.crop_tools import (
    bbox_center,
    choose_focus_region,
    clip_frames_for_timerange,
    dominant_mode,
    exponential_moving_average,
)


def run_crop_planner_agent(state: VideoJobState) -> VideoJobState:
    detections = state.get("detections", [])
    faces = state.get("face_results", [])
    ocr_regions = state.get("ocr_regions", [])
    trajectories = []
    frame_width = 1920
    frame_height = 1080
    crop_width = frame_height * (9 / 16)
    default_center_x = frame_width / 2
    default_center_y = frame_height / 2

    for clip_index, clip in enumerate(state.get("candidate_clips", [])):
        clip_frames = clip_frames_for_timerange(detections, faces, ocr_regions, clip["start"], clip["end"])
        raw_xs = []
        raw_ys = []
        modes = []
        frame_items = []
        for frame in clip_frames:
            focus_region, mode = choose_focus_region(frame, frame_width, frame_height)
            bbox = focus_region.get("bbox", [0, 0, frame_width, frame_height])
            cx, cy = bbox_center(bbox)
            cx = min(max(cx, crop_width / 2), frame_width - (crop_width / 2))
            cy = min(max(cy, frame_height / 2), frame_height / 2)
            raw_xs.append(cx)
            raw_ys.append(cy)
            modes.append(mode)
            frame_items.append(
                {
                    "ts": frame["ts"],
                    "cx": cx,
                    "cy": cy,
                    "scale": 1.0,
                    "letterbox": (bbox[2] - bbox[0]) > frame_width * 0.7,
                }
            )
        smoothed_xs = exponential_moving_average(raw_xs)
        smoothed_ys = exponential_moving_average(raw_ys)
        for item, cx, cy in zip(frame_items, smoothed_xs, smoothed_ys):
            item["cx"] = round(cx, 2)
            item["cy"] = round(cy, 2)
        trajectories.append(
            {
                "clip_index": clip_index,
                "framing_mode": dominant_mode(modes),
                "frames": frame_items
                or [
                    {
                        "ts": clip["start"],
                        "cx": default_center_x,
                        "cy": default_center_y,
                        "scale": 1.0,
                        "letterbox": True,
                    }
                ],
            }
        )

    state["crop_trajectories"] = trajectories
    state["current_step"] = "crop_planned"
    return state
