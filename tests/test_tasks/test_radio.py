from src.config import TASK_LIST
from src.tasks.radio import RADIO_TASK_NAME, get_channels


def test_radio_task_name_matches_task_list():
    assert RADIO_TASK_NAME in TASK_LIST


def test_get_channels_returns_dict_with_urls():
    channels = get_channels()
    assert "France Info" in channels
    assert channels["France Info"].startswith("http")
