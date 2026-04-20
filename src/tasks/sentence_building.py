from __future__ import annotations

import random
from typing import Any

from src.prompts import build_sentence_building_prompt
from src.tasks.base import TaskInstruction


def build(
    client: Any,
    *,
    vocab_list: list[str],
    language: str,
    level: str,
    niveau: str,
    model: str,
) -> TaskInstruction:
    selected = random.sample(vocab_list, min(len(vocab_list), 2))
    prompt = build_sentence_building_prompt(
        language=language,
        level=level,
        niveau=niveau,
        selected_vocab=selected,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}],
    )
    example = response.choices[0].message.content.strip()
    words = ", ".join(selected)
    return TaskInstruction(
        displayed_to_user=f"Baue einen Satz mit den folgenden Wörtern:\n{words}",
        internal_context={"selected_vocab": selected, "example_sentence": example},
    )
