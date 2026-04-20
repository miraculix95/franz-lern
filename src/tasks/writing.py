from __future__ import annotations

import random

from src.tasks.base import TaskInstruction


def build(*, themes: list[str], previous_theme: str) -> TaskInstruction:
    candidates = [t for t in themes if t != previous_theme]
    theme = random.choice(candidates or themes)
    return TaskInstruction(
        displayed_to_user=f"Schreibe einen Text über das Thema: {theme}",
        internal_context={"theme": theme},
    )
