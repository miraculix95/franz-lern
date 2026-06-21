"""Standalone grammar track (V2 P4 / TES-924).

On-the-fly generation for a single CEFR grammar topic, independent of any vocab
list: a short reference *explanation* and a focused *drill* whose shape is routed
by the topic's suggested exercise type. Both are plain LLM text generations in the
same idiom as the other task modules; correction of the drill reuses /correct.
"""
from __future__ import annotations

from typing import Any

from src.tasks.base import TaskInstruction

# How to phrase the drill per routed exercise type (the grammar-inventory's
# `exercise_type`). Falls back to cloze for anything unexpected.
_DRILL_INSTRUCTION = {
    "cloze": (
        "Create a short fill-in-the-blank (cloze) drill: 6 sentences (or one short "
        "paragraph) that target the grammar point. Mark each blank as ___."
    ),
    "conjugation": (
        "Create a conjugation drill: 6 short prompts (the verb plus the person / "
        "tense / mood to use) that target the grammar point, for the learner to "
        "produce the correct form."
    ),
    "transformation": (
        "Create a transformation drill: 6 sentences the learner must rewrite to "
        "practise the grammar point. State clearly how to transform each one."
    ),
    "sentence-building": (
        "Create a sentence-building drill: 6 prompts (a set of words or a short "
        "situation) the learner turns into a correct sentence practising the "
        "grammar point."
    ),
}


def explain(
    client: Any,
    *,
    language: str,
    level: str,
    topic: str,
    model: str,
    ui_language_name: str = "English",
) -> TaskInstruction:
    """A concise Markdown reference explanation of one grammar point."""
    messages = [
        {
            "role": "system",
            "content": (
                f"You are an expert {language} teacher. Explain a grammar point to a "
                f"CEFR {level} learner clearly and concisely. Write the ENTIRE "
                f"explanation in {ui_language_name}, but keep every {language} example "
                f"word/sentence in {language} (with a short {ui_language_name} gloss). "
                f"Use simple Markdown: a one-line intro, the rule in bold or a small "
                f"heading, a few bullet examples, and a short 'common mistakes' note. "
                f"Keep it tight — a quick reference, not a textbook chapter."
            ),
        },
        {
            "role": "user",
            "content": f'Explain this {language} grammar point for a {level} learner: "{topic}".',
        },
    ]
    response = client.chat.completions.create(model=model, messages=messages)
    text = (response.choices[0].message.content or "").strip()
    return TaskInstruction(
        displayed_to_user=text,
        internal_context={"topic": topic, "level": level},
    )


def drill(
    client: Any,
    *,
    language: str,
    level: str,
    topic: str,
    exercise_type: str,
    model: str,
    ui_language_name: str = "English",
) -> TaskInstruction:
    """A ready-to-solve drill focused on one grammar point, shaped by type."""
    how = _DRILL_INSTRUCTION.get(exercise_type, _DRILL_INSTRUCTION["cloze"])
    messages = [
        {
            "role": "system",
            "content": (
                f"You are an expert {language} teacher creating a focused grammar drill "
                f"for a CEFR {level} learner. The drill MUST target this grammar point: "
                f'"{topic}". Write any instructions/labels in {ui_language_name}; the '
                f"items the learner works on must be in {language} and level-appropriate. "
                f"Output ONLY the ready-to-solve drill — no answer key, no meta-commentary. "
                f"Use simple Markdown."
            ),
        },
        {"role": "user", "content": how},
    ]
    response = client.chat.completions.create(model=model, messages=messages)
    text = (response.choices[0].message.content or "").strip()
    return TaskInstruction(
        displayed_to_user=text,
        internal_context={"topic": topic, "exercise_type": exercise_type},
    )
