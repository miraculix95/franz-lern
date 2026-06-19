"""Speaking (production orale): a spoken-task brief + audio-based oral grille.

Flow:
    1. build_task() generates a short speaking task (in the UI language).
    2. The learner records themselves speaking in the browser.
    3. evaluate_audio() sends the audio to Gemini (multimodal) and scores it on
       five oral criteria — INCLUDING pronunciation & fluency, which a transcript
       alone cannot judge (that's why this path is audio-multimodal, not STT).

Only this module talks to Gemini; the rest of lingua-core uses OpenRouter. The
recorded audio (usually webm/opus from MediaRecorder) is transcoded to OGG/Opus
with ffmpeg first, because Gemini's inline audio accepts ogg/mp3/wav/flac/aac
but not webm.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any

from src.prompts import (
    build_speaking_eval_prompt,
    build_speaking_task_prompt,
)
from src.tasks.base import TaskInstruction

MAX_PER_CRITERION = 5
NUM_CRITERIA = 5
MAX_TOTAL = MAX_PER_CRITERION * NUM_CRITERIA  # 25 (4 DELF criteria + pronunciation)

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


@dataclass
class SpeakingAssessment:
    criteria: list[dict]  # [{key, label, score, comment}]
    transcript: str
    overall: str
    suggestions: list[str]

    @property
    def total(self) -> int:
        return sum(int(c.get("score", 0)) for c in self.criteria)


def build_task(
    client: Any,
    *,
    language: str,
    level: str,
    theme: str,
    model: str,
    ui_language_name: str = "English",
) -> TaskInstruction:
    """Generate the speaking task brief shown (and spoken to) the learner."""
    messages = build_speaking_task_prompt(
        language=language, level=level, theme=theme, ui_language_name=ui_language_name,
    )
    response = client.chat.completions.create(model=model, messages=messages)
    consigne = response.choices[0].message.content.strip()
    return TaskInstruction(displayed_to_user=consigne, internal_context={})


def _to_ogg(audio_bytes: bytes) -> bytes:
    """Transcode arbitrary recorded audio (webm/opus, mp4/aac, …) to OGG/Opus,
    a format Gemini's inline audio accepts. ffmpeg detects the input container."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(audio_bytes)
        inp = f.name
    try:
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", inp,
             "-vn", "-c:a", "libopus", "-b:a", "32k", "-f", "ogg", "pipe:1"],
            capture_output=True,
        )
    finally:
        try:
            os.unlink(inp)
        except OSError:
            pass
    if proc.returncode != 0 or not proc.stdout:
        detail = proc.stderr.decode("utf-8", "replace")[:300]
        raise RuntimeError(f"audio transcode failed: {detail}")
    return proc.stdout


def evaluate_audio(
    *,
    audio_bytes: bytes,
    mime_type: str,
    task: str,
    language: str,
    level: str,
    ui_language_name: str = "English",
    gemini_model: str = DEFAULT_GEMINI_MODEL,
) -> SpeakingAssessment:
    """Grade a spoken production from audio via Gemini multimodal (incl. pronunciation)."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    ogg = _to_ogg(audio_bytes)

    from google import genai
    from google.genai import types

    gclient = genai.Client(api_key=api_key)
    prompt = build_speaking_eval_prompt(
        task=task, language=language, level=level, ui_language_name=ui_language_name,
    )
    response = gclient.models.generate_content(
        model=gemini_model,
        contents=[
            prompt,
            types.Part.from_bytes(data=ogg, mime_type="audio/ogg"),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )
    payload = json.loads(response.text)
    return SpeakingAssessment(
        criteria=payload.get("criteria", []),
        transcript=payload.get("transcript", ""),
        overall=payload.get("overall", ""),
        suggestions=payload.get("suggestions", []),
    )
