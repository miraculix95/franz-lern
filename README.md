# franz-lern — AI Language Tutor

> A BYOK-first, multilingual AI language tutor built with Streamlit and OpenRouter.
> Ten exercise types including audio dictation. Mentor personas from Machiavelli to the
> Dalai Lama. Register-aware corrections from criminal slang to literary register.
> Personal project from 2025, refactored 2026 as a portfolio piece.

![status](https://img.shields.io/badge/status-personal%20project-blue)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![streamlit](https://img.shields.io/badge/streamlit-1.56%2B-red)
![tests](https://img.shields.io/badge/tests-76%20passing-brightgreen)
![license](https://img.shields.io/badge/license-MIT-green)

![hero](docs/assets/01-hero-dark.png)

## Why this exists

I built the original version in early 2025 to practice French at C1-level with a tutor
that could switch registers (Argot → Gehoben → Technisch) and imitate mentor personas
(Machiavelli, Dalai Lama, Elon Musk…). I used it daily for a while.

Then I did a [competitive analysis](2025_03_20_wettbewerbsanalyse.xlsx) (100+ competitors),
looked at Duolingo's $250M/year marketing spend and Speak's $78M funding round, and
**decided not to productize**. The software works; the market doesn't.

This repo is the honest artifact of that decision: a working personal tool, cleaned up
and modernized as a portfolio piece — including the abandoned FastAPI port (see
[experiments/](experiments/)) as a learning exhibit on what NOT to build.

## What makes it interesting

- **Sprachregister-Switching** — Slang / Vulgar / Colloquial / Standard / Formal /
  Literary / Technical. No mainstream language app models register; Mistral/Claude do,
  so this tool forces the correction feedback to match the register the learner is
  writing in.
- **Ten mentor personas** — a single dropdown switches the voice of the corrector from
  Kind Teacher to Machiavelli to Chairman Mao to Elon Musk. It's a gimmick, but the
  stylistic contrast makes errors memorable. (![personas](docs/assets/02-coach-dropdown-open.png))
- **Nine exercise types** from one shared vocabulary pool:
  writing, cloze, translation (both directions), sentence-building, error-detection,
  synonym/antonym, verb conjugation, vocabulary quiz, and **audio dictation with a
  playback-speed slider**.
- **Audio dictation (ElevenLabs)** — LLM writes a short text at the chosen CEFR level,
  ElevenLabs' Multilingual v2 speaks it, a speed slider (0.5×–1.5×) lets the learner
  replay at comprehension-pace. 36 scenarios × 6 styles injected so consecutive A1
  dictations don't repeat.
- **BYOK (Bring Your Own Key)** — users paste their OpenRouter key in the sidebar;
  keys never touch the server. Portfolio-friendly (no ops cost, no GDPR liability) and
  the architecture carries cleanly to the planned Next.js V2.
- **Four UI languages** (English / Deutsch / Français / Español) with IP-based
  auto-detection at first load, and five learning-target languages (French / English /
  Spanish / Ukrainian / German).
- **Inline `<meta-comments>`** — embed `<what does passé composé mean?>` anywhere in
  your answer; you get a side-answer without derailing the main correction.
- **Anti-cheat cloze** — structured LLM output (tools API) prevents the LLM from
  leaking solutions into the body, and an explicit shuffle rule tells the model to
  place vocabs in non-alphabetical blank positions.

## Screenshots

| Dark mode (default) | Light mode |
|---|---|
| ![dark](docs/assets/01-hero-dark.png) | ![light](docs/assets/03-hero-light.png) |

| Exercise menu | Mentor personas |
|---|---|
| ![exercises](docs/assets/04-exercises-menu.png) | ![personas](docs/assets/02-coach-dropdown-open.png) |

## Architecture

```
src/
├── app.py              Streamlit entrypoint, sidebar, task dispatch, dark-mode CSS
├── cli.py              Minimal CLI variant (writing / cloze / translation)
├── config.py           Constants (levels, mentors, themes, models, radio channels)
├── i18n.py             UI translations (EN/DE/FR/ES), IP auto-detection
├── prompts.py          All LLM prompts as pure builder functions
├── state.py            SessionState dataclass
├── vocab.py            3 vocabulary sources (file, URL, LLM-generated)
├── correction.py       Text correction + inline comment extraction
├── logging_setup.py    Central logging (replaces legacy prints)
└── tasks/              One module per exercise type (10 files + base protocol)
    ├── base.py
    ├── writing.py
    ├── cloze.py
    ├── translation.py
    ├── sentence_building.py
    ├── error_detection.py
    ├── synonym_antonym.py
    ├── conjugation.py
    ├── quiz.py         # single-call batch translation
    ├── dictation.py    # ElevenLabs TTS + variety injection
```

High-level flow: Streamlit UI → pure-function prompt builders →
`openai.OpenAI(base_url="https://openrouter.ai/api/v1")` → OpenRouter → chosen model.
Session state is consolidated in one `SessionState` dataclass. All prompts live as
pure functions so they're unit-tested without API calls via a `FakeOpenAIClient`
test double — 76 tests run in ~100ms.

## Feature matrix

| Feature                       | CLI | Streamlit | Tested | Notes                                   |
| ----------------------------- | :-: | :-------: | :----: | --------------------------------------- |
| Writing prompt + correction   |  ✅  |    ✅     |   ✅   | Mentor-style feedback                   |
| Cloze text                    |  ✅  |    ✅     |   ✅   | Structured output, anti-leak, shuffled  |
| Translation (both directions) |  ✅  |    ✅     |   ✅   | UI-lang ↔ learning-lang toggle          |
| Sentence building             |  ❌  |    ✅     |   ✅   |                                         |
| Error detection               |  ❌  |    ✅     |   ✅   |                                         |
| Synonym / antonym             |  ❌  |    ✅     |   ✅   |                                         |
| Verb conjugation              |  ❌  |    ✅     |   ✅   |                                         |
| Vocabulary quiz               |  ❌  |    ✅     |   ✅   | Fuzzy matching, single-call batch       |
| Audio dictation (ElevenLabs)  |  ❌  |    ✅     |   ✅   | Speed slider, word-by-word diff         |
| Web-article vocab extraction  |  ❌  |    ✅     |   ✅   | newspaper3k                             |
| Inline `<meta-comments>`      |  ✅  |    ✅     |   ✅   |                                         |

## Running locally

```bash
git clone https://github.com/miraculix95/franz-lern.git
cd franz-lern

uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
# Optional (local-only radio task): uv pip install -r requirements-audio.txt

cp .env.example .env
# → edit .env. Primary path: OPENROUTER_API_KEY from https://openrouter.ai/keys
# → For dictation (TTS): also ELEVENLABS_KEY from https://elevenlabs.io

# Streamlit (primary UI)
streamlit run src/app.py -- --language=französisch

# CLI (minimal, for scripting)
python -m src.cli --vocab-file data/sample_texts/vokabeln.txt --task cloze
```

The `--language` CLI flag is only the initial seed — the app has an in-sidebar
learning-language dropdown you can switch at any time.

## Model tiers

The sidebar exposes four model tiers (OpenRouter IDs):

| Tier | Model | $/correction (approx) | When |
|---|---|---:|---|
| 💰 Budget | `google/gemini-2.5-flash-lite` | $0.00017 | Default for daily use |
| ⚖️ Balanced | `anthropic/claude-haiku-4.5` | $0.00200 | Auto-selected for Ukrainian |
| 🚀 Premium | `mistralai/mistral-large-2512` | $0.00070 | Romance languages power user |
| 👑 Best | `anthropic/claude-sonnet-4.6` | $0.00600 | When cost is not a concern |

Default swaps automatically based on the learning target: Ukrainian → Haiku 4.5,
everything else → Gemini Flash Lite. See
[`research/2026-04-20-model-provider-analysis.md`](research/2026-04-20-model-provider-analysis.md)
for the full comparison including Groq latency benchmarks.

## Development

```bash
pytest                    # 76 tests, ~100ms
pytest tests/test_tasks/  # task-specific tests
ruff check src/ tests/    # lint
```

## Repository layout

```
src/                 production code
tests/               76 pure-function + fake-client tests
data/sample_texts/   corpus of French/Spanish/German texts for vocab extraction
experiments/         archived side-experiments with DISCLAIMER.md
  ├── verben_categorizer/       (one-shot LangChain utility)
  └── webapp-fastapi-abandoned/ (early auth/credits detour — security footgun gallery)
archive/legacy/      the original 2025 monolith, preserved untouched
docs/
  ├── assets/                             (screenshots for this README)
  ├── PLAN.md                             (index to superpowers plans)
  └── superpowers/plans/…                 (bite-sized implementation plans)
research/                                 (model/provider analysis)
```

## Roadmap

- [ ] **V2: Next.js + BYOK web version** — Vercel-deployed, client-side only
- [ ] **Live radio → Whisper dictation** — pull 30s of a French radio stream server-
      side, pass through Whisper, present as a dictation-style exercise. Current
      radio stub archived under `experiments/radio-task-archived/` because
      `pyaudio`-based streaming doesn't work on headless deploys.
- [ ] **Flutter shell over BYOK API** — stretch

## Lessons Learned

1. **Session-state hell is real.** 14 scattered `st.session_state` initializations in
   the legacy monolith made behavior unpredictable across reruns. One dataclass, one
   init call, problem solved.
2. **Prompts belong in pure functions.** The legacy code had prompts embedded in
   f-strings inside API-call statements — un-testable, un-reviewable side-by-side. In
   the refactor every prompt is a pure builder, unit-tested with a `FakeOpenAIClient`
   that records calls without hitting the real API.
3. **FastAPI + sqlite + hand-rolled auth was the wrong detour.** See
   [experiments/webapp-fastapi-abandoned/DISCLAIMER.md](experiments/webapp-fastapi-abandoned/DISCLAIMER.md)
   for why. If I rebuild the web version, it's Next.js + BYOK + no server-side user
   state.
4. **Localize LAST, not first.** Building Dictation + i18n in the same commit blew
   up the diff. Next time: ship feature monolingual, then i18n in a follow-up commit.
5. **Market > tech.** The hardest part wasn't building; it was admitting the
   competitive landscape was hopeless and walking away before sinking another six
   months into a market that already has Duolingo, Babbel, Speak, Loora, Praktika,
   Univerbal, and a long tail of funded competitors.
6. **LLM model choice matters more than prompt engineering for low-resource
   languages.** GPT-4o-mini hallucinated French grammar regularly (marked
   `personnes attendent` as an error — 3rd-person-plural indicative, perfectly correct).
   Switching to Mistral or Claude fixed more than any prompt tweak could.

## License

MIT.

## Author

[Bastian](https://github.com/miraculix95) — freelance AI/Python developer, Munich.
Personal tool; portfolio piece.
