# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

Active project: **lingua-app** — AI language tutor, Streamlit + OpenRouter, BYOK.
Repo: `miraculix95/lingua-app` (private). 7 learning languages, 4+ UI languages, 10+ exercise types, ~85 pure-function tests.
The original 2025 prototype (`franz-lern-streamlit.py`, `franz-lern.py`) lives untouched under `archive/legacy/` per the no-delete-archive rule.

## Run

- **Streamlit UI (primary app):** `streamlit run src/app.py -- --language=französisch`
  - `--language` seeds the target (accepted: französisch, englisch, spanisch, ukrainisch, deutsch, polnisch, hebräisch). Also switchable from the sidebar at runtime.
- **CLI variant (subset):** `python -m src.cli --vocab-file data/sample_texts/vokabeln.txt --task cloze`
- **Tests:** `pytest` (~85 tests, ~100ms, `FakeOpenAIClient` — no API calls).
- **Lint:** `ruff check src/ tests/`.

Env: `OPENROUTER_API_KEY` (primary; sidebar-BYOK overrides), optional `ELEVENLABS_KEY` for the dictation task. Shared `cc-dev/.env` or local `.env`. Dependencies pinned via `requirements.txt` + `requirements-audio.txt` (optional).

## Architecture

Modular codebase under `src/`:

- `app.py` — Streamlit entrypoint, sidebar, task dispatch, dark-mode + mobile + RTL CSS, multipage nav.
- `cli.py` — minimal CLI variant (writing / cloze / translation).
- `config.py` — constants (LEVELS, NIVEAU_LEVELS, MENTORS, THEMES, MODEL_TIERS, RTL_LANGUAGES).
- `i18n.py` — UI translations (7 UI langs) + task-name list + IP-based auto-detect.
- `prompts.py` — all LLM prompts as pure builder functions + function-call specs (cloze, reading, vocab).
- `state.py` — single `SessionState` dataclass (replaces 14 scattered `st.session_state` inits from the monolith).
- `vocab.py` — three vocab sources: file / URL (newspaper3k) / LLM-generated via tool-call.
- `correction.py` — text correction + inline `<meta-comments>` extraction.
- `logging_setup.py` — central logging.
- `tasks/` — one module per exercise type (`base.py` + `writing`, `cloze`, `translation`, `sentence_building`, `error_detection`, `synonym_antonym`, `conjugation`, `quiz`, `dictation`, `reading`).
- `pages/1_ℹ️_About.py` — secondary Streamlit page.

Flow: Streamlit UI → pure-function prompt builders → `openai.OpenAI(base_url=openrouter)` → chosen model. Session state in one dataclass; prompts unit-tested without API calls.

## Repository layout

```
src/                 production code (see above)
tests/               pure-function + fake-client tests (85 passing)
data/sample_texts/   corpus of French/Spanish/German texts for vocab extraction
research/            model/provider analysis, gap analyses
docs/                PLAN.md + superpowers/plans/…
experiments/         archived side-experiments with DISCLAIMER.md
archive/legacy/      the original 2025 monolith (franz-lern-streamlit.py, franz-lern.py)
```

## Legacy / archive

The files in `archive/legacy/` are the original 2025 prototype kept for reference (per `~/.claude/rules/no-delete-archive.md`, never delete). Do NOT run them as the primary app — the Streamlit entrypoint is `src/app.py`. They remain useful as the source of the task catalogue (`task_list`, `niveau_levels`, `mentoren`, `radio_kanale`) and the `generate_vocabulary_list` function-call schema that was ported forward.

`archive/legacy/` additionally holds `archiv_webapp_versuch/` — an abandoned FastAPI + sqlite + JWT port with a hardcoded secret and wide-open CORS. Reference-only; don't revive without a fresh security review.

## Notes

- **Models:** live model IDs are in `src/config.py` (`MODEL_TIERS`). Defaults vary per learning-target — e.g. Ukrainian auto-picks Haiku 4.5, everything else auto-picks Gemini Flash Lite. Always verify current model IDs via `ruff`/tests before assuming a model still exists.
- **Register-aware corrections** are the product's core differentiator — don't refactor the register system away.
- **BYOK-stateless** is a deliberate architecture choice — no user accounts, no server-side state. Adding persistence (SRS, fehler-journal, portfolio) requires an ADR first (see `~/.claude/rules/adr-discipline.md`).
- Match existing style (English identifiers, German inline comments where present, terse docstrings).
- `2025_03_20_wettbewerbsanalyse.xlsx` is a competitive-analysis spreadsheet, not code.
