from __future__ import annotations

from typing import Any

import streamlit as st


def render_upload_panel() -> dict[str, Any] | None:
    st.header("Convert Long-form Video to Reels")
    preferred_mode = st.selectbox("Preferred Framing Mode", ["auto", "speaker", "content", "mixed"], index=0)
    upload_tab, url_tab = st.tabs(["Upload File", "Paste URL"])
    with upload_tab:
        uploaded_file = st.file_uploader("Upload video", type=["mp4", "mov", "mkv"])
        submit_file = st.button("Generate Reels", key="generate_file")
        if submit_file and uploaded_file is not None:
            return {
                "kind": "file",
                "file_name": uploaded_file.name,
                "file_bytes": uploaded_file.getvalue(),
                "preferred_mode": preferred_mode,
            }
    with url_tab:
        url_value = st.text_input("YouTube or direct video URL")
        submit_url = st.button("Generate Reels", key="generate_url")
        if submit_url and url_value.strip():
            return {
                "kind": "url",
                "url": url_value.strip(),
                "preferred_mode": preferred_mode,
            }
    return None
