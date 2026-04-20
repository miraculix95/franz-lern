from __future__ import annotations

import random

from src.i18n import t, theme_display
from src.tasks.base import TaskInstruction


def build(
    *, themes: list[str], previous_theme: str, ui_lang: str = "en",
) -> TaskInstruction:
    candidates = [th for th in themes if th != previous_theme]
    theme_key = random.choice(candidates or themes)
    theme_shown = theme_display(theme_key, ui_lang)
    prompt_line = t("writing_task_prompt", ui_lang, theme=theme_shown)
    return TaskInstruction(
        displayed_to_user=prompt_line,
        internal_context={"theme": theme_key, "theme_display": theme_shown},
    )
