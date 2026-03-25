from __future__ import annotations

from backend.pipeline.zone2.state import VideoJobState
from backend.pipeline.zone2.tools.alignment_tools import find_visual_reference_timestamps, smooth_trajectory


def run_alignment_agent(state: VideoJobState) -> VideoJobState:
    audio_energy = state.get("audio_energy", [])
    reference_points = find_visual_reference_timestamps(state.get("transcript", []))
    aligned = []
    for trajectory in state.get("crop_trajectories", []):
        frames = [dict(frame) for frame in trajectory.get("frames", [])]
        for frame in frames:
            ts = frame["ts"]
            if any(abs(ts - point) <= 2.0 for point in reference_points):
                frame["cx"] = min(frame["cx"] + 80, 1920)
            if any(abs(ts - item["timestamp"]) <= 0.5 and item.get("is_spike") for item in audio_energy):
                frame["scale"] = 0.9
            if any(abs(ts - item["timestamp"]) <= 1.0 and item.get("is_pause") for item in audio_energy):
                frame["cx"] = (frame["cx"] * 0.6) + (1920 / 2 * 0.4)
                frame["cy"] = (frame["cy"] * 0.6) + (1080 / 2 * 0.4)
        aligned.append(
            {
                "clip_index": trajectory["clip_index"],
                "framing_mode": trajectory["framing_mode"],
                "frames": smooth_trajectory(frames),
            }
        )

    state["aligned_trajectories"] = aligned
    state["current_step"] = "aligned"
    return state
