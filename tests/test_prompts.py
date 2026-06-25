from src.prompts import (
    CLOZE_FUNCTION_SPEC,
    READING_QUESTIONS_FUNCTION_SPEC,
    VOCAB_FUNCTION_SPEC,
    VOCAB_TRANSLATION_FUNCTION_SPEC,
    build_answer_comment_prompt,
    build_cloze_messages,
    build_conjugation_prompt,
    build_correction_prompt,
    build_error_detection_prompt,
    build_literature_adapt_prompt,
    build_reading_eval_prompt,
    build_reading_questions_messages,
    build_reading_text_prompt,
    build_sentence_building_prompt,
    build_translate_prompt,
    build_translation_prompt,
    build_vocab_autogen_prompt,
    build_vocab_extract_prompt,
    build_vocab_translation_messages,
)


def test_vocab_extract_prompt_includes_level_and_count():
    p = build_vocab_extract_prompt(language="französisch", level="B2", number=30)
    assert "B2" in p
    assert "30" in p
    assert "französisch" in p


def test_translate_prompt_targets_ui_language_and_carries_text():
    msgs = build_translate_prompt(
        text="Il faisait nuit à Paris.", language="French", ui_language_name="German",
    )
    combined = " ".join(m["content"] for m in msgs)
    assert "German" in combined
    assert "French" in combined
    # the source passage rides in the user message verbatim
    assert any("Il faisait nuit à Paris." in m["content"] for m in msgs)


def test_literature_adapt_prompt_carries_passage_and_levels():
    msgs = build_literature_adapt_prompt(
        passage="Phileas Fogg était un membre du Reform-Club de Londres.",
        language="French",
        source_level="B2",
        target_level="A2",
    )
    combined = " ".join(m["content"] for m in msgs)
    assert "A2" in combined  # target level
    assert "B2" in combined  # source level
    assert "French" in combined
    # keep-the-story, not a summary/translation
    assert "summary" in combined.lower() and "translation" in combined.lower()
    # the source passage rides in the user message verbatim
    assert any("Phileas Fogg" in m["content"] for m in msgs)


def test_vocab_autogen_prompt_includes_niveau():
    p = build_vocab_autogen_prompt(language="französisch", level="B1", niveau="Technisch")
    assert "B1" in p
    assert "Technisch" in p


def test_vocab_autogen_prompt_requests_balanced_pos():
    p = build_vocab_autogen_prompt(language="französisch", level="B1", niveau="Standardsprache").lower()
    for pos in ("noun", "verb", "adjective", "adverb"):
        assert pos in p


def test_vocab_function_spec_description_mentions_balanced_word_types():
    desc = VOCAB_FUNCTION_SPEC["description"].lower()
    for pos in ("nomen", "verb", "adjektiv", "adverb"):
        assert pos in desc


def test_vocab_translation_messages_contain_words_and_target_lang():
    msgs = build_vocab_translation_messages(
        words=["maison", "courir"], learning_language="French", ui_language_name="Deutsch",
    )
    joined = " ".join(m["content"] for m in msgs)
    assert "maison" in joined
    assert "courir" in joined
    assert "Deutsch" in joined
    assert "French" in joined


def test_vocab_translation_spec_has_required_keys():
    assert VOCAB_TRANSLATION_FUNCTION_SPEC["name"] == "translate_vocabulary"
    item = VOCAB_TRANSLATION_FUNCTION_SPEC["parameters"]["properties"]["translations"]["items"]
    assert set(item["required"]) == {"word", "translation"}


def test_cloze_messages_contain_vocabs_and_trous():
    msgs = build_cloze_messages(
        language="französisch",
        level="B2",
        niveau="Standardsprache",
        selected_vocab=["maison", "voiture"],
        number_trous=4,
    )
    combined = " ".join(m["content"] for m in msgs)
    assert "maison" in combined
    assert "voiture" in combined
    assert "4" in combined
    assert "emit_cloze" in combined  # tool is mentioned by name in system prompt


def test_cloze_messages_grammar_focus_optional():
    base = build_cloze_messages(
        language="französisch", level="B2", niveau="Standardsprache",
        selected_vocab=["maison"], number_trous=4,
    )
    assert "GRAMMAR FOCUS" not in " ".join(m["content"] for m in base)

    focused = build_cloze_messages(
        language="französisch", level="B2", niveau="Standardsprache",
        selected_vocab=["maison"], number_trous=4,
        grammar_focus="the subjunctive mood",
    )
    combined = " ".join(m["content"] for m in focused)
    assert "GRAMMAR FOCUS" in combined
    assert "the subjunctive mood" in combined


def test_cloze_function_spec_has_answers_separate():
    # Answers live in their own field so they can't leak into body.
    props = CLOZE_FUNCTION_SPEC["parameters"]["properties"]
    assert "body" in props
    assert "answers" in props
    assert "title" in props


def test_translation_prompt_includes_sentences_count():
    p = build_translation_prompt(
        learning_language="French",
        ui_language_name="German",
        source_language_name="German",
        target_language_name="French",
        level="B1",
        niveau="Standardsprache",
        selected_vocab=["manger"],
        number_sentences=3,
    )
    assert "3" in p
    assert "manger" in p
    assert "German" in p and "French" in p


def test_translation_prompt_supports_reverse_direction():
    p = build_translation_prompt(
        learning_language="French",
        ui_language_name="German",
        source_language_name="French",   # reverse direction
        target_language_name="German",
        level="B1",
        niveau="Standardsprache",
        selected_vocab=["manger"],
        number_sentences=2,
    )
    # Source must be French when reversed — verifies direction parameterization.
    assert "sentences IN French" in p or "IN French" in p
    assert "INTO German" in p


def test_sentence_building_prompt_contains_words():
    p = build_sentence_building_prompt(
        language="französisch",
        level="B1",
        niveau="Standardsprache",
        selected_vocab=["maison", "voiture"],
    )
    assert "maison" in p and "voiture" in p


def test_error_detection_prompt_mentions_level():
    p = build_error_detection_prompt(
        language="französisch",
        level="B2",
        niveau="Umgangssprache",
        selected_vocab=["aller"],
    )
    assert "B2" in p and "aller" in p


def test_conjugation_prompt_is_messages_list():
    msgs = build_conjugation_prompt(language="französisch", level="B1", vocab_list=["aller"])
    assert isinstance(msgs, list)
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    assert "aller" in msgs[1]["content"]


def test_correction_prompt_includes_mentor_persona():
    p = build_correction_prompt(
        language="französisch",
        niveau="Standardsprache",
        mentor="Machiavelli",
        task="Schreibe einen Text",
        user_text="Je suis",
    )
    assert "Machiavelli" in p[0]["content"]
    assert "Je suis" in p[1]["content"]


def test_answer_comment_prompt_is_messages_list():
    msgs = build_answer_comment_prompt("Was ist passé composé?")
    assert isinstance(msgs, list)
    assert msgs[-1]["role"] == "user"
    assert "passé composé" in msgs[-1]["content"]


def test_vocab_function_spec_has_required_keys():
    assert VOCAB_FUNCTION_SPEC["name"] == "generate_vocabulary_list"
    assert "vocabulary" in VOCAB_FUNCTION_SPEC["parameters"]["properties"]


def test_reading_text_prompt_contains_theme_level_and_word_target():
    msgs = build_reading_text_prompt(
        language="French", level="B2", niveau="Standardsprache",
        theme="urbanism", word_target=350,
    )
    combined = " ".join(m["content"] for m in msgs)
    assert "B2" in combined
    assert "urbanism" in combined
    assert "350" in combined


def test_reading_questions_prompt_mentions_tool_and_counts():
    msgs = build_reading_questions_messages(
        text="Il faisait nuit à Paris.",
        language="French", ui_language_name="English",
        num_mc=5, num_open=3,
    )
    combined = " ".join(m["content"] for m in msgs)
    assert "emit_reading_questions" in combined
    assert "5" in combined and "3" in combined
    # Questions/options/answers are written in the LEARNING language now (#13),
    # like a real comprehension exam — not translated into the UI language.
    assert "French" in combined
    assert "Do NOT translate" in combined


def test_reading_questions_spec_declares_mc_and_open():
    props = READING_QUESTIONS_FUNCTION_SPEC["parameters"]["properties"]
    assert "multiple_choice" in props
    assert "open_questions" in props
    mc_item_props = props["multiple_choice"]["items"]["properties"]
    assert "options" in mc_item_props
    assert "correct_index" in mc_item_props
    open_item_props = props["open_questions"]["items"]["properties"]
    assert "reference_answer" in open_item_props


def test_reading_eval_prompt_asks_for_verdict_first_line():
    msgs = build_reading_eval_prompt(
        text="T", question="Q?", reference_answer="R",
        user_answer="A", language="French", ui_language_name="English",
    )
    combined = " ".join(m["content"] for m in msgs)
    assert "CORRECT" in combined and "PARTIAL" in combined and "INCORRECT" in combined
    assert "R" in combined
    assert "English" in combined
