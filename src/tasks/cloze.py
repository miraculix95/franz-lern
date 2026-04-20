from __future__ import annotations

import json
import random
from typing import Any

from src.i18n import t
from src.prompts import CLOZE_FUNCTION_SPEC, build_cloze_messages
from src.tasks.base import TaskInstruction


def build(
    client: Any,
    *,
    vocab_list: list[str],
    language: str,
    level: str,
    niveau: str,
    number_trous: int,
    model: str,
    ui_lang: str = "en",
    ui_language_name: str = "English",
) -> TaskInstruction:
    """Generate a cloze exercise with two anti-cheat mitigations."""
    selected = random.sample(vocab_list, min(len(vocab_list), number_trous))
    messages = build_cloze_messages(
        language=language,
        level=level,
        niveau=niveau,
        selected_vocab=selected,
        number_trous=number_trous,
        ui_language_name=ui_language_name,
    )
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=[{"type": "function", "function": CLOZE_FUNCTION_SPEC}],
        tool_choice={"type": "function", "function": {"name": "emit_cloze"}},
    )
    tool_call = response.choices[0].message.tool_calls[0]
    payload = json.loads(tool_call.function.arguments)

    title = payload["title"]
    vocab_hints = payload.get("vocab_hints", [])
    body = payload["body"]
    answers = payload["answers"]

    display_vocab = sorted(selected, key=str.lower)

    displayed = (
        f"**{title}**\n\n"
        f"**{t('cloze_vocab_heading', ui_lang)}**\n"
        + "\n".join(f"- {h}" for h in vocab_hints)
        + f"\n\n**{t('cloze_use_these', ui_lang)}:** {', '.join(display_vocab)}\n\n"
        f"**{t('cloze_text_heading', ui_lang)}**\n\n{body}"
    )

    return TaskInstruction(
        displayed_to_user=displayed,
        internal_context={
            "selected_vocab": selected,
            "answers": answers,
            "body": body,
            "title": title,
        },
    )
