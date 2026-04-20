from src.tasks.synonym_antonym import build


def test_build_picks_one_vocab():
    result = build(vocab_list=["maison", "voiture"])
    assert result.internal_context["selected_vocab"] in ["maison", "voiture"]
    assert result.internal_context["selected_vocab"] in result.displayed_to_user
