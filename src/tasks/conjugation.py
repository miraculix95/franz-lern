from __future__ import annotations

import random
from typing import Any

from src.i18n import t
from src.prompts import build_conjugation_prompt
from src.tasks.base import TaskInstruction

PERSONS = ["ich", "du", "er/sie/es", "wir", "ihr", "sie"]


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
    messages = build_conjugation_prompt(language=language, level=level, vocab_list=vocab_list)
    response = client.chat.completions.create(model=model, messages=messages)
    verb = response.choices[0].message.content.strip().lower()
    person = random.choice(PERSONS)
    text = t("conjugation_task_prompt", ui_lang, verb=verb, person=person)
    return TaskInstruction(
        displayed_to_user=text,
        internal_context={"verb": verb, "person": person},
    )
