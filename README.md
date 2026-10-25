# Nexora

A full-stack AI chat assistant: React + Vite frontend, FastAPI backend, SQLite history, and a real LLM via an OpenAI-compatible API.

## Features
- Real LLM responses with conversation context
- Multiple persisted conversations (SQLite)
- Markdown + syntax-highlighted code blocks
- Light/dark theme, responsive layout
- Retry, copy, rename, delete conversations
- Health check and settings modal

## Project structure

```
PE_PROJECT/
  backend/
    app/
      main.py
      api/routes/{health,chat,conversations}.py
      core/config.py
      schemas/
      services/{llm_service,conversation_service}.py
      db/{database,models}.py
    tests/
    requirements.txt
    .env.example
  frontend/
    src/...
  README.md
```

## Prerequisites
- Python 3.9+
- Node.js 18+

## Backend setup

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# edit .env and set LLM_API_KEY (and optionally LLM_MODEL, LLM_BASE_URL)
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: `curl http://127.0.0.1:8000/api/health`

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to the backend.

## Environment variables (backend/.env)

| Variable | Description |
|---|---|
| LLM_PROVIDER | Provider name (default openai) |
| LLM_MODEL | Model name (default gpt-4o-mini) |
| LLM_BASE_URL | Optional OpenAI-compatible base URL |
| LLM_API_KEY | API key (required for real responses) |
| LLM_TIMEOUT_SECONDS | Request timeout (default 60) |
| LLM_MAX_OUTPUT_TOKENS | Max output tokens (default 1024) |
| LLM_CONTEXT_MESSAGE_LIMIT | Context messages (default 20) |
| DATABASE_URL | SQLite URL (default sqlite:///./app.db) |
| CORS_ORIGINS | Allowed origins (default http://localhost:5173) |

Never commit `.env`. The API key is never sent to the browser.

## Running tests

Backend:
```bash
cd backend
.venv/bin/pytest -q
```

Frontend:
```bash
cd frontend
npm run test
npm run build
```

## Common errors
- `configured: false` in /api/health: set LLM_API_KEY in backend/.env and restart.
- CORS errors: ensure CORS_ORIGINS includes the frontend origin.
- `no such table`: delete stale app.db and restart; tests use in-memory DB.

## Limitations
- Single-user, local-only; no authentication.
- Depends on configured provider availability and API key.
- Model answers may be incorrect; verify important information.
