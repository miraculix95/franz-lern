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


def test_build_test_shuffles_but_keeps_correct_option():
    # Correct option carries a recognizable marker; after the in-code shuffle the
    # correct_index must still point to that exact option (defends against "always A").
    qs = []
    for level in LEVELS:
        qs.append({
            "level": level,
            "question": f"q-{level}",
            "options": [f"RIGHT-{level}", "w1", "w2", "w3"],  # correct at index 0 from the LLM
            "correct_index": 0,
        })
    fake = FakeOpenAIClient(responses=[{"tool_arguments": json.dumps({"questions": qs})}])
    out = build_test(fake, language="French", model="m")
    assert len(out) == len(LEVELS)
    for q in out:
        assert q["options"][q["correct_index"]] == f"RIGHT-{q['level']}"


def test_recommend_level_counts_correct_not_prefix():
    qs = [_q(level, ci=1) for level in LEVELS]  # correct option is index 1 for all
    assert recommend_level(qs, [1, 1, 1, 1, 1, 1]) == "C2"   # 6 correct
    # 5 correct with a gap at B1 → C1 (NOT A2): a single miss must not cap the result
    assert recommend_level(qs, [1, 1, 0, 1, 1, 1]) == "C1"
    assert recommend_level(qs, [1, 1, 1, 0, 0, 0]) == "B1"   # 3 correct → B1
    assert recommend_level(qs, [1, 0, 0, 0, 0, 0]) == "A1"   # 1 correct → A1
    assert recommend_level(qs, [0, 0, 0, 0, 0, 0]) == "A1"   # 0 correct → A1
    assert recommend_level(qs, [1, 1, 0, 0, 0, 0]) == "A2"   # 2 correct → A2
    assert recommend_level(qs, [None, 1, 1, 1, 1, 1]) == "C1"  # 5 answered+correct → C1


def test_recommend_level_empty():
    assert recommend_level([], []) == "A1"
