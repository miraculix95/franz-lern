from __future__ import annotations

import random
from typing import Any

from src.prompts import build_translation_prompt
from src.tasks.base import TaskInstruction


def build(
    client: Any,
    *,
    vocab_list: list[str],
    language: str,  # learning language in English (e.g. "French")
    level: str,
    niveau: str,
    number_sentences: int,
    model: str,
    ui_language_name: str = "English",
    direction: str = "to_learning",  # "to_learning" or "to_native"
) -> TaskInstruction:
    selected = random.sample(vocab_list, min(len(vocab_list), 3))
    if direction == "to_learning":
        source, target = ui_language_name, language
    else:
        source, target = language, ui_language_name
    prompt = build_translation_prompt(
        learning_language=language,
        ui_language_name=ui_language_name,
        source_language_name=source,
        target_language_name=target,
        level=level,
        niveau=niveau,
        selected_vocab=selected,
        number_sentences=number_sentences,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}],
    )
    body = response.choices[0].message.content.strip()
    return TaskInstruction(
        displayed_to_user=body,
        internal_context={"selected_vocab": selected},
    )
