# ⚠️ Abandoned Experiment — Do Not Use

This folder is an early-2025 attempt to port the Streamlit app to a FastAPI + sqlite web service. It was **abandoned** because the architecture took a direction we did not want to pursue (auth/credits system), and the implementation has multiple security foot-guns that should never see production.

## Known issues (intentionally not fixed — file is archived as-is for portfolio honesty)

- `SECRET_KEY = "supersecret"` is hardcoded in `backend/main.py`
- Passwords are stored in **plaintext** in `users.db` (`backend/database.py`)
- JWTs are created with `expires = datetime.now()` — they are always already expired
- CORS is configured `allow_origins=["*"]` **with** `allow_credentials=True`, which browsers reject
- `init_db()` is called from both `database.py` and `main.py`
- Windows-x64 SQLite DLLs shipped in the folder (irrelevant on Linux servers)

## Why it's kept in the repo

Portfolio honesty: showing what was tried and why it was stopped is more informative
than pretending only the successful path existed. The Streamlit version (in `src/`) is
the surviving, maintained implementation.
