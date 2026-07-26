"""Managed OpenRouter client for the lingua-core API (no BYOK — server-side key).

V2 abandons BYOK (the target audience has no API keys), so the service uses one
server-side OpenRouter key. Mirrors V1's _build_client (base_url = OpenRouter).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# .env lives at the repo root (one level up from api/).
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

DEFAULT_MODEL = "anthropic/claude-haiku-4.5"


# Ohne explizites max_tokens rechnet OpenRouter beim Affordability-Check mit dem
# Modell-Maximum (z.B. 64k) — bei niedrigem Guthaben blockt dann JEDER Call mit
# 402, obwohl reale Antworten winzig sind (Vorfall 2026-07-26, TES-1019). Kein
# lingua-core-Output braucht auch nur annähernd 8k Tokens.
DEFAULT_MAX_TOKENS = 8000


def build_client() -> OpenAI:
    key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set (managed key required in V2).")
    client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")

    # Zentral statt an ~30 Call-Sites: max_tokens defaulten, Caller-Werte gewinnen.
    original_create = client.chat.completions.create

    def create_with_default(*args, **kwargs):
        kwargs.setdefault("max_tokens", DEFAULT_MAX_TOKENS)
        return original_create(*args, **kwargs)

    client.chat.completions.create = create_with_default  # type: ignore[method-assign]
    return client


def elevenlabs_key() -> str:
    """Managed ElevenLabs key for TTS (listening / dictation)."""
    return (
        os.environ.get("ELEVENLABS_KEY")
        or os.environ.get("ELEVENLABS_API_KEY")
        or ""
    ).strip()
