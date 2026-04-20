from __future__ import annotations

import random

from src.tasks.base import TaskInstruction


def build(*, vocab_list: list[str]) -> TaskInstruction:
    selected = random.choice(vocab_list)
    return TaskInstruction(
        displayed_to_user=f"Finde die Synonyme und Antonyme von: {selected}",
        internal_context={"selected_vocab": selected},
    )
