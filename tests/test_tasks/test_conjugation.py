from src.tasks.conjugation import PERSONS, build
from tests.fake_openai import FakeOpenAIClient


def test_build_picks_verb_and_person():
    fake = FakeOpenAIClient(responses=["aller"])
    result = build(
        fake,
        vocab_list=["maison", "aller"],
        language="französisch",
        level="B1",
        niveau="Standardsprache",
        model="gpt-4o-mini",
    )
    assert "aller" in result.displayed_to_user
    assert result.internal_context["person"] in PERSONS
    assert "Präsens" in result.displayed_to_user
