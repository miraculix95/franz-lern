from src.tasks.quiz import build_quiz, score_answers
from tests.fake_openai import FakeOpenAIClient


def test_build_quiz_returns_translations_in_one_call():
    import json
    payload = {"translations": {"maison": "Haus", "voiture": "Auto", "chaise": "Stuhl"}}
    fake = FakeOpenAIClient(responses=[{"tool_arguments": json.dumps(payload)}])
    quiz = build_quiz(
        fake,
        vocab_list=["maison", "voiture", "chaise"],
        language="French",
        count=3,
        model="google/gemini-2.5-flash-lite",
        ui_language_name="German",
    )
    assert set(quiz.keys()) == {"maison", "voiture", "chaise"}
    # ONE API call for the whole quiz — not one per word.
    assert len(fake.calls) == 1
    # Uses tools API:
    assert "tools" in fake.calls[0]


def test_build_quiz_caps_at_vocab_size():
    import json
    fake = FakeOpenAIClient(responses=[{"tool_arguments": json.dumps({"translations": {"maison": "Haus"}})}])
    quiz = build_quiz(
        fake,
        vocab_list=["maison"],
        language="French",
        count=10,
        model="google/gemini-2.5-flash-lite",
    )
    assert len(quiz) == 1


def test_score_answers_counts_correct_case_insensitive():
    # Quiz dict: {learning-lang word: UI-lang translation}. UI shows the
    # translation as the prompt, user types back the learning-lang word.
    quiz = {"maison": "Haus", "voiture": "Auto"}
    user_answers = {"maison": "MAISON", "voiture": "faux"}
    result = score_answers(quiz, user_answers)
    assert result.correct == 1
    assert result.total == 2
    assert result.per_word == {"maison": True, "voiture": False}


def test_score_answers_tolerates_missing_answer():
    quiz = {"maison": "Haus"}
    result = score_answers(quiz, {})
    assert result.correct == 0
    assert result.per_word == {"maison": False}


def test_score_accepts_trailing_punctuation():
    quiz = {"maison": "Haus"}
    assert score_answers(quiz, {"maison": "maison."}).per_word["maison"] is True
    assert score_answers(quiz, {"maison": "Maison!"}).per_word["maison"] is True


def test_score_accepts_leading_article():
    quiz = {"maison": "Haus"}
    assert score_answers(quiz, {"maison": "la maison"}).per_word["maison"] is True
    assert score_answers(quiz, {"maison": "die Maus"}).per_word["maison"] is False  # wrong word


def test_score_tolerates_single_typo():
    quiz = {"voiture": "Auto"}
    # "voitur" — one missing char, ratio > 0.85
    assert score_answers(quiz, {"voiture": "voitur"}).per_word["voiture"] is True


def test_score_rejects_unrelated_word():
    quiz = {"voiture": "Auto"}
    assert score_answers(quiz, {"voiture": "maison"}).per_word["voiture"] is False
