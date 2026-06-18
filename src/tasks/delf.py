"""DELF production-écrite task: a text-type consigne + grille-based assessment.

Flow:
    1. build() generates a DELF-style consigne (text type + word count + context).
    2. The learner writes their text in the UI.
    3. evaluate() scores it against the four DELF criteria (each 0–5) via the
       emit_delf_assessment tool, returning structured per-criterion feedback.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from src.prompts import (
    DELF_GRILLE_FUNCTION_SPEC,
    build_delf_eval_messages,
    build_delf_task_prompt,
)
from src.tasks.base import TaskInstruction

MAX_PER_CRITERION = 5
NUM_CRITERIA = 4
MAX_TOTAL = MAX_PER_CRITERION * NUM_CRITERIA  # 20


@dataclass
class DelfAssessment:
    criteria: list[dict]  # [{key, label, score, comment}]
    word_count: int
    overall: str
    suggestions: list[str]

    @property
    def total(self) -> int:
        return sum(int(c.get("score", 0)) for c in self.criteria)


def build(
    client: Any,
    *,
    language: str,
    level: str,
    text_type_en: str,
    word_target: int,
    theme: str,
    model: str,
    ui_language_name: str = "English",
) -> TaskInstruction:
    """Generate a DELF writing consigne (the brief shown to the learner)."""
    messages = build_delf_task_prompt(
        language=language, level=level, text_type_en=text_type_en,
        word_target=word_target, theme=theme, ui_language_name=ui_language_name,
    )
    response = client.chat.completions.create(model=model, messages=messages)
    consigne = response.choices[0].message.content.strip()
    return TaskInstruction(
        displayed_to_user=consigne,
        internal_context={"text_type_en": text_type_en, "word_target": word_target},
    )


def evaluate(
    client: Any,
    *,
    task: str,
    user_text: str,
    language: str,
    level: str,
    text_type_en: str,
    word_target: int,
    model: str,
    ui_language_name: str = "English",
) -> DelfAssessment:
    """Grade a written production against the DELF grid (structured tool call)."""
    messages = build_delf_eval_messages(
        task=task, user_text=user_text, language=language, level=level,
        text_type_en=text_type_en, word_target=word_target,
        ui_language_name=ui_language_name,
    )
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=[{"type": "function", "function": DELF_GRILLE_FUNCTION_SPEC}],
        tool_choice={"type": "function", "function": {"name": "emit_delf_assessment"}},
    )
    payload = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    return DelfAssessment(
        criteria=payload.get("criteria", []),
        word_count=int(payload.get("word_count", 0)),
        overall=payload.get("overall", ""),
        suggestions=payload.get("suggestions", []),
    )
