from __future__ import annotations

import streamlit as st


def render_transcript_viewer(transcript: dict, selected_clip_ranges: list[tuple[float, float]]) -> None:
    with st.expander("View Full Transcript"):
        for segment in transcript.get("segments", []):
            start = float(segment.get("start", 0.0))
            end = float(segment.get("end", 0.0))
            selected = any(clip_start <= start <= clip_end or clip_start <= end <= clip_end for clip_start, clip_end in selected_clip_ranges)
            label = f"[{start:06.2f} - {end:06.2f}] {segment.get('text', '')}"
            if selected:
                st.code(label)
            else:
                st.text(label)
