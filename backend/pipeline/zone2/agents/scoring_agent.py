from __future__ import annotations

import json
from typing import Any

from backend.config import get_settings
from backend.pipeline.zone2.state import VideoJobState
from backend.pipeline.zone2.tools.scoring_tools import score_segment, transcript_snippet


settings = get_settings()


def _llm_reason(segment: dict[str, Any], score: float) -> str:
    prompt = (
        "Write one short reason for why this transcript segment could work as a short-form reel. "
        "Base it only on the transcript text. "
        f"Score: {score}. Text: {segment.get('text', '')}"
    )
    try:
        from langchain_ollama import ChatOllama

        llm = ChatOllama(base_url=settings.ollama_base_url, model="llama3", temperature=0)
        response = llm.invoke(prompt)
        return response.content.strip() or "Strong transcript hook with clear payoff."
    except Exception:
        text = segment.get("text", "").strip()
        opener = text.split(".")[0][:90]
        return f"Strong hook around: {opener or 'a concise tutorial moment'}"


def run_scoring_agent(state: VideoJobState) -> VideoJobState:
    segments = state.get("segments", [])
    audio_energy = state.get("audio_energy", [])
    scored = []
    for segment in segments:
        score = score_segment(segment, audio_energy)
        scored.append(
            {
                "start": segment.get("start", 0.0),
                "end": segment.get("end", 0.0),
                "score": score,
                "segment": segment,
                "transcript_snippet": transcript_snippet(segment),
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)
    top_candidates = scored[:15]
    candidate_clips = []
    for item in top_candidates[: settings.max_clips_per_job]:
        candidate_clips.append(
            {
                "start": item["start"],
                "end": item["end"],
                "score": item["score"],
                "reason": _llm_reason(item["segment"], item["score"]),
                "transcript_snippet": item["transcript_snippet"],
            }
        )
    state["candidate_clips"] = candidate_clips
    state["current_step"] = "scoring_complete"
    return state
