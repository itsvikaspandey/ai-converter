from __future__ import annotations

import time
from typing import Any

import streamlit as st

from frontend.api_client import APIClient


def render_progress_tracker(client: APIClient, job_id: str) -> dict[str, Any]:
    placeholder = st.empty()
    last_status: dict[str, Any] = {}
    while True:
        last_status = client.get_job_status(job_id)
        with placeholder.container():
            st.subheader("Processing")
            st.progress(last_status.get("progress_percent", 0) / 100)
            st.caption(last_status.get("current_step", "Queued"))
            if last_status.get("estimated_seconds_remaining") is not None:
                st.write(f"Estimated time remaining: {last_status['estimated_seconds_remaining']}s")
            if last_status.get("status") == "failed":
                st.error("\n".join(last_status.get("errors", ["Job failed"])))
                if st.button("Retry", key=f"retry_{job_id}"):
                    st.rerun()
                return last_status
        if last_status.get("status") == "complete":
            return last_status
        time.sleep(3)
