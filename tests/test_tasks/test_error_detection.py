from src.tasks.error_detection import build
from tests.fake_openai import FakeOpenAIClient


def test_build_prefixes_with_task_label():
    fake = FakeOpenAIClient(responses=["1. Il vas. 2. Je avons. 3. Nous est."])
    result = build(
        fake,
        vocab_list=["aller", "avoir", "être"],
        language="französisch",
        level="B1",
        niveau="Standardsprache",
        model="gpt-4o-mini",
    )
    d = result.displayed_to_user
    assert "Fehler" in d or "korrigiere" in d
