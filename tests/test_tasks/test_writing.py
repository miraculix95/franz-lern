from src.tasks.writing import build


def test_build_returns_task_with_theme():
    result = build(themes=["Urlaub", "Sport"], previous_theme="Sport")
    assert "Urlaub" in result.displayed_to_user
    assert result.internal_context["theme"] == "Urlaub"


def test_build_avoids_previous_theme():
    result = build(themes=["A", "B"], previous_theme="A")
    assert result.internal_context["theme"] == "B"


def test_build_picks_from_all_when_no_previous():
    result = build(themes=["A", "B", "C"], previous_theme="")
    assert result.internal_context["theme"] in ["A", "B", "C"]
