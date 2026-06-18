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
import random
from typing import Any

from src.config import LEVELS  # ["A1","A2","B1","B2","C1","C2"]
from src.prompts import PLACEMENT_FUNCTION_SPEC, build_placement_messages


def _shuffle_options(q: dict) -> dict:
    """Shuffle a question's options and re-point correct_index.

    LLMs tend to park the correct answer at index 0; shuffling in code
    guarantees the correct option is evenly distributed regardless.
    """
    opts = list(q.get("options", []))
    ci = q.get("correct_index", 0)
    if not opts or not (0 <= ci < len(opts)):
        return q
    correct = opts[ci]
    random.shuffle(opts)
    return {**q, "options": opts, "correct_index": opts.index(correct)}


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
    # Keep only known CEFR levels, ordered as in LEVELS; shuffle each item's options.
    order = {lvl: i for i, lvl in enumerate(LEVELS)}
    return sorted(
        [_shuffle_options(q) for q in questions if q.get("level") in order],
        key=lambda q: order[q["level"]],
    )


def recommend_level(questions: list[dict], answers: list[int | None]) -> str:
    """Map the NUMBER of correct answers to a CEFR level.

    With one question per level (A1→C2), N correct answers → the N-th level
    (min A1). This is robust to a single shaky/ambiguous question: getting 5 of
    6 right yields C1, not A2 — a gap in the middle no longer caps the result.
    """
    if not questions:
        return LEVELS[0]
    correct = sum(
        1
        for i, q in enumerate(questions)
        if i < len(answers) and answers[i] is not None and answers[i] == q.get("correct_index")
    )
    idx = max(0, min(len(LEVELS) - 1, correct - 1))
    return LEVELS[idx]
