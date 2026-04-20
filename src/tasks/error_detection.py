from __future__ import annotations

import random
from typing import Any

from src.i18n import t
from src.prompts import build_error_detection_prompt
from src.tasks.base import TaskInstruction


def build(
    client: Any,
    *,
    vocab_list: list[str],
    language: str,
    level: str,
    niveau: str,
    model: str,
    ui_lang: str = "en",
) -> TaskInstruction:
    selected = random.sample(vocab_list, min(len(vocab_list), 5))
    prompt = build_error_detection_prompt(
        language=language,
        level=level,
        niveau=niveau,
        selected_vocab=selected,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}],
    )
    body = response.choices[0].message.content.strip()
    return TaskInstruction(
        displayed_to_user=f"{t('error_task_prompt', ui_lang)}\n\n{body}",
        internal_context={"selected_vocab": selected, "body": body},
    )
