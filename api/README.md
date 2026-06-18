# lingua-core (V2 Phase 0)

FastAPI service that re-uses the V1 Streamlit app's Python logic (`src/`) behind
HTTP, so the V2 Next.js frontend can call it without re-implementing prompts,
grading, DELF grille or the placement test. **V1 stays untouched** — this runs
as a separate process on its own port.

Managed key model (no BYOK): set `OPENROUTER_API_KEY` in the repo-root `.env`.

## Run (from repo root, V1 venv)

```bash
.venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8557
```

## Endpoints (Phase 0 — one per task shape)

`GET /health` · `POST /vocab/generate` · `POST /generate/cloze` ·
`POST /generate/transformation` · `POST /correct` · `POST /delf/task` ·
`POST /delf/evaluate` · `POST /reading/text` · `POST /reading/questions` ·
`POST /placement/test` · `POST /placement/recommend`

Remaining exercise types (writing, sentence, error, synonym, conjugation,
dictation, listening) are mechanical additions in Phase 2.

See `../konzept/architektur-v2.md` and Linear epic TES-923.
