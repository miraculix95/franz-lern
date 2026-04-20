from src.tasks.sentence_building import build
from tests.fake_openai import FakeOpenAIClient


def test_build_contains_selected_words():
    fake = FakeOpenAIClient(responses=["Ein Beispielsatz."])
    result = build(
        fake,
        vocab_list=["maison", "voiture", "chaise"],
        language="französisch",
        level="B1",
        niveau="Standardsprache",
        model="gpt-4o-mini",
    )
    displayed = result.displayed_to_user
    assert "maison" in displayed or "voiture" in displayed or "chaise" in displayed
