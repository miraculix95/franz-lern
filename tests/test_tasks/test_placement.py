import json

from src.tasks.placement import build_test, recommend_level
from tests.fake_openai import FakeOpenAIClient

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def _q(level, ci=0):
    return {"level": level, "question": f"q-{level}", "options": ["a", "b", "c", "d"], "correct_index": ci}


def test_build_test_orders_and_filters_levels():
    qs = [_q("B1"), _q("A1"), _q("ZZ"), _q("C2"), _q("A2"), _q("B2"), _q("C1")]
    fake = FakeOpenAIClient(responses=[{"tool_arguments": json.dumps({"questions": qs})}])
    out = build_test(fake, language="French", model="m")
    assert [q["level"] for q in out] == LEVELS  # bogus level dropped, sorted A1→C2
    assert fake.calls[0]["tool_choice"]["function"]["name"] == "emit_placement_test"


def test_recommend_level_longest_correct_prefix():
    qs = [_q(level, ci=1) for level in LEVELS]  # correct option is index 1 for all
    assert recommend_level(qs, [1, 1, 1, 1, 1, 1]) == "C2"   # all correct
    assert recommend_level(qs, [1, 1, 1, 0, 1, 1]) == "B1"   # gap at B2 caps at B1
    assert recommend_level(qs, [0, 1, 1, 1, 1, 1]) == "A1"   # first wrong → A1
    assert recommend_level(qs, [None, 1, 1, 1, 1, 1]) == "A1"  # unanswered first → A1


def test_recommend_level_empty():
    assert recommend_level([], []) == "A1"
