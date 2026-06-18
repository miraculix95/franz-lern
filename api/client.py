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


def build_client() -> OpenAI:
    key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set (managed key required in V2).")
    return OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")
