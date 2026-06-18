"""CEFR placement test: a 6-item quiz (one per level A1–C2) that estimates the
learner's level so the app can set it for them.

Flow:
    1. build_test() → 6 MC questions, one per CEFR level, in the target language.
    2. The UI collects one answer per question.
    3. recommend_level() walks A1 → C2 and returns the highest level the learner
       answered correctly without a gap (longest correct prefix), min A1.
"""
from __future__ import annotations

import json
from typing import Any

from src.config import LEVELS  # ["A1","A2","B1","B2","C1","C2"]
from src.prompts import PLACEMENT_FUNCTION_SPEC, build_placement_messages


def build_test(client: Any, *, language: str, model: str) -> list[dict]:
    """Return the placement questions ordered A1 → C2 (one per level)."""
    messages = build_placement_messages(language=language)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=[{"type": "function", "function": PLACEMENT_FUNCTION_SPEC}],
        tool_choice={"type": "function", "function": {"name": "emit_placement_test"}},
    )
    payload = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    questions = payload.get("questions", [])
    # Keep only known CEFR levels, ordered as in LEVELS.
    order = {lvl: i for i, lvl in enumerate(LEVELS)}
    return sorted(
        [q for q in questions if q.get("level") in order],
        key=lambda q: order[q["level"]],
    )


def recommend_level(questions: list[dict], answers: list[int | None]) -> str:
    """Longest correct prefix from A1 upward → that level (min A1).

    A gap (wrong answer) caps the recommendation at the last consecutively
    correct level, so a single miss at B2 with A1–B1 correct yields B1.
    """
    if not questions:
        return LEVELS[0]
    recommended = LEVELS[0]
    for i, q in enumerate(questions):
        picked = answers[i] if i < len(answers) else None
        if picked is not None and picked == q.get("correct_index"):
            recommended = q.get("level", recommended)
        else:
            break
    return recommended
