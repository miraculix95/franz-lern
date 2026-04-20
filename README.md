# franz-lern — AI Language Tutor

> GPT-powered French/multilingual language tutor with mentor personas, register switching,
> 9 exercise types, and live French radio dictation. Streamlit app; Next.js + BYOK web
> version planned.

![status](https://img.shields.io/badge/status-personal%20project-blue)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![streamlit](https://img.shields.io/badge/streamlit-1.30%2B-red)
![tests](https://img.shields.io/badge/tests-53%20passing-brightgreen)
![license](https://img.shields.io/badge/license-MIT-green)

## Why this exists

I built this in early 2025 to practice French at C1-level with a tutor that could
switch registers (Argot → Vornehm → Technisch) and imitate mentor personas
(Machiavelli, Dalai Lama, Elon Musk…). I used it daily for a while.

Then I did a [competitive analysis](2025_03_20_wettbewerbsanalyse.xlsx) (100+ competitors),
looked at Duolingo's $250M marketing spend and Speak's $78M funding round, and
**decided not to productize**. The software works; the market doesn't.

This repo is the honest artifact of that decision: a working personal tool, cleaned
up as a portfolio piece — including the abandoned FastAPI port (see
[experiments/](experiments/)) as a learning exhibit.

## What makes it interesting

- **Sprachregister-Switching** (Argot / Vulgär / Umgangssprache / Standardsprache /
  Gehoben / Hohe Literatur / Technisch) — no mainstream language app does this.
- **Mentor Personas** — a single prompt-switch changes the voice of the corrector
  from "Netter Lehrer" to Machiavelli to Chairman Mao. Gimmick, but memorable.
- **9 exercise types** from a single shared vocabulary pool (cloze, translation,
  sentence-building, error-detection, synonym/antonym, verb conjugation, writing,
  vocabulary quiz, **live radio dictation**).
- **Inline `<meta-comments>`** — type `<was heißt Passé Composé?>` inline in your
  answer, get a side-answer separately from the main correction.
- **BYOK-first (planned V2)** — the polished web version will use client-side OpenAI
  calls with the user's key, no server-side custody.

## Architecture

See [docs/assets/ARCHITECTURE.md](docs/assets/ARCHITECTURE.md) for the module graph.

High-level: Streamlit UI → pure-function prompt builders → OpenAI API. Session state
is consolidated in one `SessionState` dataclass. All prompts live in `src/prompts.py`
as pure functions so they're trivially unit-testable without API calls (via a
`FakeOpenAIClient` test double).

## Feature matrix

| Feature                       | CLI | Streamlit | Tested | Notes                           |
| ----------------------------- | :-: | :-------: | :----: | ------------------------------- |
| Writing prompt + correction   |  ✅  |    ✅     |   ✅   |                                 |
| Cloze text                    |  ✅  |    ✅     |   ✅   |                                 |
| Translation exercises         |  ✅  |    ✅     |   ✅   |                                 |
| Sentence building             |  ❌  |    ✅     |   ✅   |                                 |
| Error detection               |  ❌  |    ✅     |   ✅   |                                 |
| Synonym / antonym             |  ❌  |    ✅     |   ✅   |                                 |
| Verb conjugation              |  ❌  |    ✅     |   ✅   |                                 |
| Vocabulary quiz               |  ❌  |    ✅     |   ✅   | Fixed from broken legacy impl   |
| Live French radio             |  ❌  |    ✅     |   ⚠️   | Local audio only (pyaudio)      |
| Web-article vocab extraction  |  ❌  |    ✅     |   ✅   | via newspaper3k                 |
| Inline `<meta-comments>`      |  ✅  |    ✅     |   ✅   |                                 |

## Running locally

```bash
git clone https://github.com/miraculix95/franz-lern.git
cd franz-lern

uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

cp .env.example .env
# → edit .env, paste your OPENAI_API_KEY

# Streamlit (primary UI)
streamlit run src/app.py -- --language=französisch

# CLI (minimal, for scripting)
python -m src.cli --vocab-file data/sample_texts/vokabeln.txt --task cloze
```

## Development

```bash
pytest                    # all tests (53 passing, ~0.1s)
pytest tests/test_tasks/  # only task tests
ruff check src/ tests/    # lint
```

## Repository layout

```
src/             production code (app.py, cli.py, config, prompts, vocab, correction, state, tasks/)
tests/           53 pure-function + fake-client tests
data/sample_texts/   corpus of French/Spanish/German texts for vocab extraction
experiments/     archived side-experiments with DISCLAIMER.md (verben_categorizer, webapp-fastapi-abandoned)
archive/legacy/  the original 2025 monolith, preserved untouched for history
docs/            architecture diagram, implementation plans
```

## Roadmap

- [ ] **V2: Next.js + BYOK web version** — polished client-side-only web UI on Vercel
- [ ] **Radio transcription** — Whisper integration so the radio task produces a
      transcript to ask questions against (the legacy code read `radio_text.txt`
      but nothing ever wrote it)
- [ ] **Optional Supabase progress tracking** (only if V2 lands)
- [ ] **Mobile: Flutter shell over the BYOK API** (stretch)

## Lessons Learned

1. **Session-state hell is real.** 14 scattered `st.session_state` initializations
   in the legacy monolith made behavior unpredictable across reruns. One
   dataclass, one init call, end of problem.
2. **Prompts belong in pure functions.** The legacy code had prompts embedded in
   f-strings inside API-call statements — un-testable, impossible to review
   side-by-side. Moving them to `src/prompts.py` as pure builders means they can
   be diffed, unit-tested, and reused across CLI and web.
3. **FastAPI + sqlite + hand-rolled auth was the wrong detour.** See
   [experiments/webapp-fastapi-abandoned/DISCLAIMER.md](experiments/webapp-fastapi-abandoned/DISCLAIMER.md)
   for why that version was stopped. If I rebuild, it's Next.js + BYOK + no
   server-side user state.
4. **Market > tech.** The hardest part wasn't building; it was admitting the
   competitive landscape was hopeless and walking away before sinking another
   six months into a market that already has Duolingo, Babbel, Speak, Loora,
   Praktika, Univerbal and a long tail of funded competitors.

## License

MIT.

## Author

[Bastian](https://github.com/miraculix95) — freelance AI/Python developer, Munich.
Personal tool, portfolio piece.
