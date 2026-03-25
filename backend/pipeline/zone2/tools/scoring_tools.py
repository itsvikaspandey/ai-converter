from __future__ import annotations

import re
from typing import Any


HOOK_WORDS = {"discover", "stop", "never", "always", "why", "how"}
TECH_TERM_PATTERN = re.compile(r"\b(api|model|llm|python|sql|docker|vector|agent|gpu|ffmpeg|langgraph|redis)\b", re.IGNORECASE)


def score_segment(segment: dict[str, Any], audio_energy: list[dict[str, Any]]) -> float:
    text = segment.get("text", "").strip()
    words = text.split()
    if not words:
        return 0.0

    score = 0.0
    first_three = " ".join(words[:3]).lower()
    if text.endswith("?") or first_three.startswith(("why", "how", "what")):
        score += 2
    if words[0].rstrip(":").isdigit() or words[0].lower() in HOOK_WORDS:
        score += 2
    start = float(segment.get("start", 0.0))
    end = float(segment.get("end", start))
    first_three_seconds_end = min(end, start + 3.0)
    if any(start <= item["timestamp"] <= first_three_seconds_end and item.get("is_spike") for item in audio_energy):
        score += 2
    if any(start <= item["timestamp"] <= end and item.get("is_pause") for item in audio_energy):
        score += 1
    density = len(TECH_TERM_PATTERN.findall(text)) / max(len(words), 1)
    if density > 0.3:
        score += 1
    if not text.endswith((".", "!", "?")):
        score -= 2
    return max(0.0, min(10.0, score))


def transcript_snippet(segment: dict[str, Any], max_chars: int = 160) -> str:
    text = segment.get("text", "").strip()
    return text if len(text) <= max_chars else text[: max_chars - 3].rstrip() + "..."
