from __future__ import annotations

import random

from src.i18n import t
from src.tasks.base import TaskInstruction


def build(*, vocab_list: list[str], ui_lang: str = "en") -> TaskInstruction:
    selected = random.choice(vocab_list)
    return TaskInstruction(
        displayed_to_user=f"{t('synant_task_prompt', ui_lang)} {selected}",
        internal_context={"selected_vocab": selected},
    )
