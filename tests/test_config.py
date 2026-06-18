from src.config import (
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    DEFAULT_MODEL_UK,
    DEFAULT_TRANSFORMATION,
    GRAMMAR_FOCI,
    INPUT_KEYBOARD_URL,
    LANGUAGES,
    LEVELS,
    MENTORS,
    MODEL_TIERS,
    MODELS,
    NIVEAU_LEVELS,
    NON_LATIN_LANGUAGES,
    RTL_LANGUAGES,
    THEMES,
    TRANSFORMATIONS,
    default_model_for_language,
)


def test_levels_are_cefr():
    assert LEVELS == ["A1", "A2", "B1", "B2", "C1", "C2"]


def test_languages_contain_core_set():
    for lang in ["französisch", "englisch", "spanisch", "deutsch"]:
        assert lang in LANGUAGES


def test_default_model_is_in_models_list():
    assert DEFAULT_MODEL in MODELS


def test_default_language_is_in_languages():
    assert DEFAULT_LANGUAGE in LANGUAGES


def test_niveau_levels_spans_register_range():
    assert "Standardsprache" in NIVEAU_LEVELS
    assert "Technisch" in NIVEAU_LEVELS


def test_mentors_list_not_empty():
    assert len(MENTORS) >= 5


def test_themes_list_not_empty():
    assert len(THEMES) >= 5


def test_no_deprecated_models():
    # gpt-4-0613 was retired; anything hardcoded to it would break silently.
    assert "gpt-4-0613" not in MODELS


def test_model_tiers_point_to_valid_openrouter_ids():
    # OpenRouter IDs always have provider/model shape
    for tier, model_id in MODEL_TIERS.items():
        assert "/" in model_id, f"{tier}: {model_id} missing provider prefix"


def test_default_model_uk_is_haiku():
    # Ukrainian keeps its own override hook (DEFAULT_MODEL_UK), but currently shares
    # Claude Haiku 4.5 with the general default. The separate constant lets us bump
    # UK to a bigger model later without touching the rest.
    assert DEFAULT_MODEL_UK == "anthropic/claude-haiku-4.5"


def test_default_model_for_language_swaps_on_ukrainian():
    assert default_model_for_language("französisch") == DEFAULT_MODEL
    assert default_model_for_language("ukrainisch") == DEFAULT_MODEL_UK
    assert default_model_for_language("englisch") == DEFAULT_MODEL


def test_transformations_have_default_and_mixed():
    assert DEFAULT_TRANSFORMATION in TRANSFORMATIONS
    assert "mixed" in TRANSFORMATIONS
    # every transformation carries a non-empty English prompt phrase
    assert all(isinstance(v, str) and v.strip() for v in TRANSFORMATIONS.values())


def test_grammar_foci_have_prompt_phrases():
    assert len(GRAMMAR_FOCI) >= 5
    assert all(isinstance(v, str) and v.strip() for v in GRAMMAR_FOCI.values())
    # 'none' is a UI sentinel, never a real focus key
    assert "none" not in GRAMMAR_FOCI


def test_input_keyboard_urls_cover_non_latin_languages():
    # The input-help trigger set must be real learning languages, and the two
    # RTL languages (Arabic, Hebrew) must be a subset of it.
    assert set(INPUT_KEYBOARD_URL) == set(NON_LATIN_LANGUAGES)
    for lang in INPUT_KEYBOARD_URL:
        assert lang in LANGUAGES, f"{lang} not a learning language"
    for lang, url in INPUT_KEYBOARD_URL.items():
        assert url.startswith("https://"), f"{lang}: {url} not https"
    assert RTL_LANGUAGES <= set(NON_LATIN_LANGUAGES)
    # Latin-script languages must NOT trigger the hint.
    for lang in ["französisch", "englisch", "spanisch", "deutsch", "polnisch"]:
        assert lang not in NON_LATIN_LANGUAGES
