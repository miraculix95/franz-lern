"""Narrow content safety floor for lingua-core.

lingua's stance is **censor-free for adults**: explicit/adult topics are allowed
(a learner may legitimately want explicit vocabulary). This module enforces the
ONE non-negotiable, legally-required exception — sexual content involving minors
(CSAM). Nothing else is classified here; "offensive" in general is NOT blocked.

The check runs only on USER FREE-TEXT (custom themes / custom grammar focus).
It is FAIL-CLOSED for this one category: on ambiguity or classifier error it
returns blocked, because a legal floor must not silently fail open. Free-text is
also never pooled cross-user (see the v2 content cache), so a false positive only
costs the requester one rejected attempt.
"""
from __future__ import annotations

from typing import Any

_SYSTEM = (
    "You are a NARROW safety classifier for a language-learning app. The app "
    "ALLOWS adult and explicit topics — adult sexual themes, profanity, violence, "
    "drugs, politics are all ALLOWED and must be classified OK. You flag exactly "
    "ONE thing: input that requests or describes sexual content involving minors "
    "/ children (CSAM), or that sexualises minors in any way. If and only if the "
    "input falls in that single category, answer BLOCK. For everything else "
    "answer OK. Answer with exactly one word: BLOCK or OK."
)


def is_illegal_minor_sexual(client: Any, *, text: str, model: str) -> bool:
    """True only when the input requests sexual content involving minors.

    Fail-closed: blocks on classifier error or empty/ambiguous BLOCK signal,
    because this is a legal floor. Returns False for empty input (nothing to
    generate from)."""
    t = (text or "").strip()
    if not t:
        return False
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": t},
            ],
            temperature=0,
            max_tokens=3,
        )
        out = (resp.choices[0].message.content or "").strip().upper()
        return out.startswith("BLOCK")
    except Exception:
        # Legal floor must not fail open: if we cannot classify, block.
        return True
