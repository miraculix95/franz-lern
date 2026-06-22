"""Dictation task: LLM generates text → ElevenLabs TTS → audio for learner.

Flow:
    1. Ask the learning-language LLM for a short coherent text.
    2. Pipe it through ElevenLabs Multilingual v2 for speech.
    3. Return bytes + original text; UI plays the audio with a speed slider
       and hides the text until the learner clicks "reveal".
"""
from __future__ import annotations

import random
from typing import Any

import requests

from src.logging_setup import get_logger
from src.prompts import (
    DICTATION_SCENARIOS,
    DICTATION_STYLES,
    build_dictation_text_prompt,
)
from src.tasks.base import TaskInstruction

log = get_logger(__name__)

# Bella — warm, clear, works well across EN/FR/DE/ES/IT/PT multilingual.
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# ElevenLabs `speed` accepts 0.7–1.2 (default 1.0); below 1.0 the voice articulates
# *naturally* slower (with real pauses), which is far better for beginners than
# stretching a fast recording client-side. Per CEFR level — A1 as slow as allowed,
# up to slightly-above-native at C2. The v2 player's playback slider stays for
# personal fine-tuning on top of this baseline.
TTS_SPEED_MIN, TTS_SPEED_MAX = 0.7, 1.2
_SPEED_BY_LEVEL = {
    "A1": 0.7, "A2": 0.8, "B1": 0.9, "B2": 1.0, "C1": 1.1, "C2": 1.2,
}


def speed_for_level(level: str | None) -> float:
    """CEFR level → ElevenLabs generation speed, clamped to the valid range."""
    return _SPEED_BY_LEVEL.get((level or "").upper(), 1.0)


class TTSUnavailable(RuntimeError):
    """Raised when no ElevenLabs key is configured or the API call fails."""


def generate_text(
    client: Any,
    *,
    language: str,
    level: str,
    niveau: str,
    model: str,
    sentences: int = 3,
    avoid_recent: list[str] | None = None,
    theme: str = "",
) -> str:
    """Generate a dictation text with heavy variety injection.

    Strategy:
    - Random scenario + random style per call (from module lists in prompts.py).
    - High temperature so the model actually diverges between calls.
    - Optional ``avoid_recent``: last N dictation texts — passed to the prompt
      so the model has a concrete negative context and doesn't repeat.
    """
    scenario = random.choice(DICTATION_SCENARIOS)
    style = random.choice(DICTATION_STYLES)
    messages = build_dictation_text_prompt(
        language=language, level=level, niveau=niveau, sentences=sentences,
        scenario=scenario, style=style,
    )
    if theme:
        messages.append({
            "role": "user",
            "content": (
                f"The text must be about the theme: {theme}. "
                f"Keep the specified level, register and length."
            ),
        })
    if avoid_recent:
        joined = "\n\n".join(f"- {t[:200]}" for t in avoid_recent[-3:])
        messages.append({
            "role": "user",
            "content": (
                f"IMPORTANT: do NOT produce a text that resembles any of these "
                f"previously-generated dictations (different opening, different "
                f"vocabulary, different scenario focus):\n\n{joined}"
            ),
        })
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.9,
    )
    return response.choices[0].message.content.strip()


def synthesize_speech(
    text: str,
    *,
    api_key: str,
    voice_id: str = DEFAULT_VOICE_ID,
    model_id: str = "eleven_multilingual_v2",
    speed: float = 1.0,
    timeout: float = 30.0,
) -> bytes:
    """Call ElevenLabs TTS, return raw MP3 bytes.

    ``speed`` (0.7–1.2) sets the generation pace; values are clamped to the
    valid range so a level mapping can't push the API into a 422.

    Raises TTSUnavailable on auth / network / quota errors so the UI can
    gracefully show a fallback message without crashing.
    """
    if not api_key:
        raise TTSUnavailable("No ELEVENLABS_KEY configured.")
    speed = max(TTS_SPEED_MIN, min(TTS_SPEED_MAX, speed))
    url = ELEVENLABS_TTS_URL.format(voice_id=voice_id)
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "speed": speed,
        },
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=timeout)
    except requests.exceptions.RequestException as exc:
        log.warning("ElevenLabs network error: %s", exc)
        raise TTSUnavailable(f"Network error: {exc}") from exc
    if r.status_code != 200:
        log.warning("ElevenLabs HTTP %s: %s", r.status_code, r.text[:200])
        raise TTSUnavailable(f"HTTP {r.status_code}: {r.text[:200]}")
    return r.content


def build(
    client: Any,
    *,
    language: str,
    level: str,
    niveau: str,
    model: str,
    elevenlabs_key: str,
    sentences: int = 3,
) -> TaskInstruction:
    """Produce a dictation instruction with audio bytes in the context."""
    text = generate_text(
        client, language=language, level=level, niveau=niveau, model=model,
        sentences=sentences,
    )
    audio_bytes = synthesize_speech(
        text, api_key=elevenlabs_key, speed=speed_for_level(level),
    )
    return TaskInstruction(
        displayed_to_user="",  # UI shows audio player, not the text, until reveal
        internal_context={"text": text, "audio": audio_bytes},
    )
