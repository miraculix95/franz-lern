from src.tasks.translation import build
from tests.fake_openai import FakeOpenAIClient


def test_build_includes_sentence_count():
    fake = FakeOpenAIClient(responses=["1. Satz\n2. Satz\n3. Satz"])
    result = build(
        fake,
        vocab_list=["maison", "voiture"],
        language="französisch",
        level="B1",
        niveau="Standardsprache",
        number_sentences=3,
        model="gpt-4o-mini",
    )
    assert result.displayed_to_user
    assert "3" in fake.calls[0]["messages"][0]["content"]
