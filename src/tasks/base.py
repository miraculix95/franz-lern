"""Task-module protocol.

Every concrete task (cloze, translation, …) exports a function
``build(client, **params) -> TaskInstruction``. The returned object carries
everything the UI needs to render the exercise.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaskInstruction:
    displayed_to_user: str
    internal_context: dict | None = None
