from src.tasks.error_detection import build
from tests.fake_openai import FakeOpenAIClient


def test_build_prefixes_with_task_label():
    fake = FakeOpenAIClient(responses=["1. Il vas. 2. Je avons. 3. Nous est."])
    result = build(
        fake,
        vocab_list=["aller", "avoir", "être"],
        language="French",
        level="B1",
        niveau="Standardsprache",
        model="google/gemini-2.5-flash-lite",
        ui_lang="en",
    )
    d = result.displayed_to_user
    assert "Find" in d or "fix" in d or "errors" in d
