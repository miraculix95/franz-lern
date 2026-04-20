"""Live French radio streaming task.

KNOWN LIMITATIONS:

- Requires local audio output (pyaudio/PortAudio). Does NOT work on Streamlit
  Cloud / any headless server. The Streamlit UI gracefully shows a note when
  pyaudio is missing.
- Transcription step is a stub: the legacy code reads ``radio_text.txt`` but
  nothing in the pipeline writes it. Transcription via Whisper is a follow-up
  item (see README Roadmap section).

The streaming function itself lives here; the long-running loop is called from
the Streamlit handler in app.py.

Task name is kept in sync with ``src.config.TASK_LIST`` via ``RADIO_TASK_NAME``
(fixes Linear TES-541 — legacy had two names, UI never matched handler).
"""
from __future__ import annotations

from src.config import RADIO_CHANNELS

RADIO_TASK_NAME = "Radio hören und aufnehmen"


def get_channels() -> dict[str, str]:
    return dict(RADIO_CHANNELS)


def is_audio_available() -> bool:
    """Check if pyaudio can open an output device. False on headless servers."""
    try:
        import pyaudio  # noqa: F401

        p = pyaudio.PyAudio()
        try:
            if p.get_device_count() == 0:
                return False
            return True
        finally:
            p.terminate()
    except Exception:
        return False
