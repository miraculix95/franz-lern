from src.tasks.transformation import build
from tests.fake_openai import FakeOpenAIClient


def test_build_carries_transformation_and_samples_vocab():
    fake = FakeOpenAIClient(responses=["Apply passive voice:\n1) ...\n2) ..."])
    result = build(
        fake,
        vocab_list=["manger", "chat", "souris", "maison"],
        language="französisch",
        level="B1",
        niveau="Standardsprache",
        number_sentences=2,
        transformation_en="rewrite each sentence switching between active and passive voice",
        model="gpt-4o-mini",
    )
    assert result.displayed_to_user == "Apply passive voice:\n1) ...\n2) ..."
    assert result.internal_context["transformation"].startswith("rewrite each sentence")
    selected = result.internal_context["selected_vocab"]
    assert set(selected) <= {"manger", "chat", "souris", "maison"}
    assert len(selected) == 2  # min(len(vocab), max(number_sentences, 1))


def test_build_handles_more_sentences_than_vocab():
    fake = FakeOpenAIClient(responses=["x"])
    result = build(
        fake, vocab_list=["a", "b"], language="französisch", level="A2",
        niveau="Standardsprache", number_sentences=5, transformation_en="mix", model="m",
    )
    # never samples more than the vocab list holds
    assert len(result.internal_context["selected_vocab"]) == 2
