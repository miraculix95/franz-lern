"""Vocabulary quiz — fixed re-implementation of the broken legacy version.

Legacy bugs that are fixed here (see Linear TES-540):

- ``answer = [], word = []`` was Tuple-unpacking, not two lists.
- ``enumerate(quiz.items())`` yields 2-tuples not 3; the legacy for-loop crashed.
- Button-callback referenced undefined Streamlit keys.

Single-call optimization (2026-04-20): translations fetched for all words in a
single tool-call rather than N sequential completions. Cuts quiz-build time
from ~10s to ~1-2s.
"""
from __future__ import annotations

import difflib
import json
import random
import re
from dataclasses import dataclass
from typing import Any

_ARTICLES = {
    # German
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "einer",
    # English
    "a", "an", "the",
    # French
    "le", "la", "les", "un", "une", "des", "l'", "du", "de",
    # Spanish
    "el", "los", "las", "una", "unos", "unas",
    # Ukrainian: no articles (skip)
}

_PUNCT_RE = re.compile(r"[^\w\s'-]", re.UNICODE)

_FUZZY_THRESHOLD = 0.85  # 0.9 was too strict for short words (Autoo vs Auto = 0.888)


def _normalize(s: str) -> str:
    """Lowercase, strip punctuation, drop leading articles."""
    s = _PUNCT_RE.sub(" ", s.lower()).strip()
    tokens = s.split()
    if tokens and tokens[0] in _ARTICLES:
        tokens = tokens[1:]
    return " ".join(tokens).strip()


def _is_match(user: str, expected: str, threshold: float = _FUZZY_THRESHOLD) -> bool:
    """Fuzzy match: exact after normalization OR SequenceMatcher ratio ≥ threshold."""
    u = _normalize(user)
    e = _normalize(expected)
    if not u:
        return False
    if u == e:
        return True
    return difflib.SequenceMatcher(None, u, e).ratio() >= threshold


@dataclass
class QuizResult:
    correct: int
    total: int
    per_word: dict[str, bool]


_QUIZ_FUNCTION_SPEC: dict = {
    "name": "emit_quiz_translations",
    "description": "Return translations of each input word into the target language.",
    "parameters": {
        "type": "object",
        "properties": {
            "translations": {
                "type": "object",
                "description": (
                    "Map from source word (as given) to translated word. "
                    "Value is a single word in the target language, no article, "
                    "no explanation, no punctuation."
                ),
                "additionalProperties": {"type": "string"},
            }
        },
        "required": ["translations"],
    },
}


def build_quiz(
    client: Any,
    *,
    vocab_list: list[str],
    language: str,
    count: int,
    model: str,
    ui_language_name: str = "English",
) -> dict[str, str]:
    """Build a quiz dict {source_word: target_translation} in a single API call."""
    selected = random.sample(vocab_list, min(len(vocab_list), count))
    joined = ", ".join(selected)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You translate {language} words into {ui_language_name}. "
                    f"Use the emit_quiz_translations tool. For each given word, return "
                    f"the single most common {ui_language_name} word — no article, "
                    f"no explanation, no punctuation."
                ),
            },
            {
                "role": "user",
                "content": f"Translate these {language} words into {ui_language_name}: {joined}",
            },
        ],
        tools=[{"type": "function", "function": _QUIZ_FUNCTION_SPEC}],
        tool_choice={"type": "function", "function": {"name": "emit_quiz_translations"}},
    )
    tool_call = response.choices[0].message.tool_calls[0]
    payload = json.loads(tool_call.function.arguments)
    raw = payload["translations"]
    # Preserve the selected-word order, even if the LLM reorders keys.
    return {word: raw.get(word, "").strip() for word in selected}


def score_answers(quiz: dict[str, str], user_answers: dict[str, str]) -> QuizResult:
    """Score a quiz tolerantly.

    The quiz dict is {learning-language word: UI-language translation}. The UI
    shows the UI-language translation as the prompt ("What is the French word
    for 'entwickeln'?") and expects the user to type the learning-language
    word back — so we compare the user's answer against the dict *key*, not
    the value. The value is prompt-display only.

    Accepts:
    - exact match after normalization (case, punctuation, leading articles)
    - fuzzy match with difflib ratio ≥ 0.85 (one typo OK, unrelated word NOT)
    """
    per_word = {
        word: _is_match(user_answers.get(word, ""), word)
        for word in quiz.keys()
    }
    return QuizResult(
        correct=sum(per_word.values()),
        total=len(quiz),
        per_word=per_word,
    )
