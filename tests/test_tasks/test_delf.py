import json

from src.tasks.delf import MAX_TOTAL, DelfAssessment, build, evaluate
from tests.fake_openai import FakeOpenAIClient


def test_build_returns_consigne_and_carries_params():
    fake = FakeOpenAIClient(responses=["  Écris un email à un ami pour…  "])
    instr = build(
        fake, language="French", level="B1", text_type_en="an email",
        word_target=120, theme="vacances", model="m",
    )
    assert instr.displayed_to_user == "Écris un email à un ami pour…"
    assert instr.internal_context["word_target"] == 120
    combined = " ".join(m["content"] for m in fake.calls[0]["messages"])
    assert "an email" in combined and "120" in combined


def test_evaluate_parses_grille_and_totals():
    payload = {"tool_arguments": json.dumps({
        "criteria": [
            {"key": "consigne", "label": "Respect de la consigne", "score": 4, "comment": "ok"},
            {"key": "coherence", "label": "Cohérence", "score": 3, "comment": "ok"},
            {"key": "lexicon", "label": "Lexique", "score": 5, "comment": "ok"},
            {"key": "grammar", "label": "Grammaire", "score": 2, "comment": "ok"},
        ],
        "word_count": 118, "overall": "Bien dans l'ensemble.", "suggestions": ["a", "b"],
    })}
    fake = FakeOpenAIClient(responses=[payload])
    a = evaluate(
        fake, task="consigne…", user_text="mon texte", language="French", level="B1",
        text_type_en="an email", word_target=120, model="m",
    )
    assert isinstance(a, DelfAssessment)
    assert a.total == 14
    assert a.total <= MAX_TOTAL
    assert a.word_count == 118
    assert len(a.criteria) == 4
    assert len(a.suggestions) == 2
    # graded via the structured tool
    assert fake.calls[0]["tool_choice"]["function"]["name"] == "emit_delf_assessment"
