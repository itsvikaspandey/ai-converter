from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.api_client import APIClient


BADGE_BY_MODE = {
    "speaker": "Speaker",
    "content": "Content",
    "mixed": "Mixed",
}


def _score_color(score: float) -> str:
    if score > 7:
        return "green"
    if score >= 4:
        return "orange"
    return "red"


def render_clip_card(client: APIClient, clip: dict[str, Any]) -> bool:
    preview_url = f"{client.base_url}{clip['preview_url']}" if clip.get("preview_url") else None
    if preview_url:
        st.video(preview_url)
    st.markdown(
        f"<span style='color:{_score_color(float(clip['score']))};font-weight:600'>Score {clip['score']:.1f}</span>",
        unsafe_allow_html=True,
    )
    st.caption(BADGE_BY_MODE.get(clip.get("framing_mode", "mixed"), "Mixed"))
    st.write(clip.get("reason", ""))
    st.caption(f"*{clip.get('transcript_snippet', '')}*")

    selected = st.checkbox("Select for export", key=f"select_{clip['clip_id']}")
    if st.button("Export Full Quality", key=f"export_{clip['clip_id']}"):
        export_result = client.export_clip(str(clip["clip_id"]))
        st.success(f"Export ready: {export_result.get('export_url')}")

    with st.expander("Edit Crop"):
        mode = st.selectbox(
            "Framing mode",
            ["auto", "speaker", "content", "mixed"],
            index=["auto", "speaker", "content", "mixed"].index(clip.get("framing_mode", "mixed"))
            if clip.get("framing_mode", "mixed") in ["auto", "speaker", "content", "mixed"]
            else 0,
            key=f"mode_{clip['clip_id']}",
        )
        start_end = st.slider(
            "Trim window",
            min_value=max(0.0, float(clip["start"]) - 5.0),
            max_value=float(clip["end"]) + 5.0,
            value=(float(clip["start"]), float(clip["end"])),
            key=f"trim_{clip['clip_id']}",
        )
        transcript_text = st.text_area(
            "Editable transcript",
            value=clip.get("transcript_snippet", ""),
            key=f"transcript_{clip['clip_id']}",
        )
        if st.button("Apply Changes", key=f"apply_{clip['clip_id']}"):
            with st.spinner("Re-rendering clip preview..."):
                client.override_clip(
                    str(clip["clip_id"]),
                    {
                        "framing_mode": mode,
                        "crop_overrides": [],
                        "start_time": start_end[0],
                        "end_time": start_end[1],
                        "transcript_text": transcript_text,
                    },
                )
            st.success("Override submitted. Refreshing preview on next rerun.")
    return selected
