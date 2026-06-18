from __future__ import annotations

import random
from typing import Any

from src.prompts import build_transformation_prompt
from src.tasks.base import TaskInstruction


def build(
    client: Any,
    *,
    vocab_list: list[str],
    language: str,  # learning language in English (e.g. "French")
    level: str,
    niveau: str,
    number_sentences: int,
    transformation_en: str,
    model: str,
    ui_language_name: str = "English",
) -> TaskInstruction:
    """Sentence-transformation drill — a free-answer task graded by the shared
    correction flow. The model writes N source sentences + a rewriting rule;
    the learner submits the transformed sentences."""
    selected = random.sample(vocab_list, min(len(vocab_list), max(number_sentences, 1)))
    prompt = build_transformation_prompt(
        language=language,
        level=level,
        niveau=niveau,
        selected_vocab=selected,
        number_sentences=number_sentences,
        transformation_en=transformation_en,
        ui_language_name=ui_language_name,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}],
    )
    body = response.choices[0].message.content.strip()
    return TaskInstruction(
        displayed_to_user=body,
        internal_context={"selected_vocab": selected, "transformation": transformation_en},
    )
