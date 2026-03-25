from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.api_client import APIClient
from frontend.components.clip_card import render_clip_card


def render_clips_dashboard(client: APIClient, clips: list[dict[str, Any]]) -> None:
    st.header("Generated Reels - pick and export")
    selected_clip_ids: list[str] = []
    for index in range(0, len(clips), 2):
        columns = st.columns(2)
        for column, clip in zip(columns, clips[index : index + 2]):
            with column:
                if render_clip_card(client, clip):
                    selected_clip_ids.append(str(clip["clip_id"]))
    if st.button("Export All Selected") and selected_clip_ids:
        for clip_id in selected_clip_ids:
            client.export_clip(clip_id)
        st.success(f"Queued exports for {len(selected_clip_ids)} clip(s).")
