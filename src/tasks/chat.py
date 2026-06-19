"""Conversation chat with inline correction — the lightest exercise.

The learner chats in the target language; each turn the model (a) replies
naturally to keep the conversation going and (b) corrects the learner's latest
message if needed. Both come back in one structured tool call.
"""
from __future__ import annotations

import json
from typing import Any

from src.prompts import CHAT_FUNCTION_SPEC, build_chat_messages


def respond(
    client: Any,
    *,
    history: list[dict],
    language: str,
    niveau: str,
    model: str,
    ui_language_name: str = "English",
) -> dict:
    """Return {'reply', 'correction'} for the latest learner message."""
    messages = build_chat_messages(
        history=history, language=language, niveau=niveau,
        ui_language_name=ui_language_name,
    )
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=[{"type": "function", "function": CHAT_FUNCTION_SPEC}],
        tool_choice={"type": "function", "function": {"name": "emit_chat_turn"}},
    )
    payload = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    return {
        "reply": payload.get("reply", ""),
        "correction": payload.get("correction", ""),
    }
