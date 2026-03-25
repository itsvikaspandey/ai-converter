from __future__ import annotations

import os

import streamlit as st

from frontend.api_client import APIClient
from frontend.components.clips_dashboard import render_clips_dashboard
from frontend.components.progress_tracker import render_progress_tracker
from frontend.components.transcript_viewer import render_transcript_viewer
from frontend.components.upload_panel import render_upload_panel


st.set_page_config(page_title="AI Reels Converter", layout="wide")
client = APIClient(base_url=os.getenv("BACKEND_URL", "http://backend:8000"))

if "job_id" not in st.session_state:
    st.session_state.job_id = None

submission = render_upload_panel()
if submission:
    with st.spinner("Creating job..."):
        if submission["kind"] == "file":
            result = client.create_job_from_file(submission["file_name"], submission["file_bytes"], submission["preferred_mode"])
        else:
            result = client.create_job_from_url(submission["url"], submission["preferred_mode"])
    st.session_state.job_id = result["job_id"]
    st.rerun()

job_id = st.session_state.job_id
if job_id:
    status = render_progress_tracker(client, job_id)
    if status.get("status") == "complete":
        clips = client.get_job_clips(job_id)
        render_clips_dashboard(client, clips)
        transcript = client.get_transcript(job_id)
        render_transcript_viewer(transcript, [(clip["start"], clip["end"]) for clip in clips])
