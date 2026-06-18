# lingua-core (V2) — FastAPI wrapper around the V1 src/ logic.
# Build context is the repo root (needs both api/ and src/).
FROM python:3.12-slim

WORKDIR /app

# Deps first for layer caching.
COPY api/requirements-docker.txt ./api/requirements-docker.txt
RUN pip install --no-cache-dir -r api/requirements-docker.txt

# App code: the reused V1 logic + the API layer.
COPY src ./src
COPY api ./api

EXPOSE 8080
# OPENROUTER_API_KEY and LINGUA_CORE_TOKEN come from the environment (compose .env).
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
