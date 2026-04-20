from __future__ import annotations

import random
from typing import Any

from src.prompts import build_translation_prompt
from src.tasks.base import TaskInstruction


def build(
    client: Any,
    *,
    vocab_list: list[str],
    language: str,
    level: str,
    niveau: str,
    number_sentences: int,
    model: str,
) -> TaskInstruction:
    selected = random.sample(vocab_list, min(len(vocab_list), 3))
    prompt = build_translation_prompt(
        language=language,
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
