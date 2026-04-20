# Radio Task — Archived 2026-04-20

Moved out of `src/tasks/` because the feature was never more than a stub:
it showed the raw stream URL and required local `pyaudio` to do anything, which
doesn't work on any realistic deploy target (Streamlit Cloud, Vercel, a headless VPS).

## Why not just delete it

The concept is actually the most original idea in the whole app — native-pace
comprehension training via real French radio streams. Worth keeping the code as
reference when the feature is rebuilt properly.

## How to bring it back (future roadmap item)

The right implementation is **Whisper-on-demand**, not `pyaudio`:

1. User clicks "Record 30s" in the UI.
2. Server-side Python pulls 30s of the icecast stream via `requests` (no audio
   output needed — we never play it locally).
3. Hand the buffer to OpenAI Whisper or ElevenLabs Speech-to-Text.
4. Return the transcript as a dictation-style exercise.

This way the feature works headless, no `pyaudio`/`portaudio` dependency, and
the "listening" step becomes the learner's own headphones on whatever device.

Linear: TES-551 (archived as Option B). Option A is the Whisper rebuild above.

## Files

- `radio.py` — original stub with `is_audio_available()`, `get_channels()`,
  `RADIO_TASK_NAME = "Radio hören und aufnehmen"`
- `test_radio.py` — tests for the above

Both moved unchanged. Import paths would need updating if revived.
