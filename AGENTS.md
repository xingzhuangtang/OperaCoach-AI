# AGENTS.md

This file provides guidance to the AI agent when working with code in this repository.

## Project Overview
Opera (Beijing Opera/Kunqu etc.) AI coaching MVP. Users upload singing videos/audio, the system intelligently slices them and visualizes results.

- **Backend**: FastAPI + SQLAlchemy + SQLite (PostgreSQL via Docker optional)
- **Frontend**: Vue 3 + TypeScript + Vite + Element Plus
- **AI**: DashScope Fun-ASR (lyrics extraction) + Librosa (audio slicing) + MoviePy (audio extraction from video)

## Commands

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
cd frontend && npm run build   # includes vue-tsc type checking

# PostgreSQL (optional, default is SQLite)
docker compose up -d
```

## Architecture

**Data model**: `OperaWork` → `OperaSegment` → `SegmentSlice`

**API routes** (`/api/v1`):
- `auth` — register/login (phone + SHA-256 hashed password, JWT 7-day expiry)
- `upload` — video/audio upload + audio extraction from video (files stored in `backend/uploads/`)
- `segments` — opera work/segment management + audio slicing + lyrics extraction

**Lyrics extraction**: Uses DashScope Fun-ASR (not Whisper). Requires `DASHSCOPE_API_KEY` in `backend/.env`.

## Gotchas

1. **DB tables auto-create on startup** (`main.py:17`) — no migration tool needed
2. **Duplicate route definitions** in `segments.py` — `/works/{work_id}` DELETE and `/by-work/{work_id}` GET are defined multiple times (lines 43-101). FastAPI uses the first definition; duplicates are dead code
3. **No test framework** — no pytest or any test config exists
4. **No linting/formatting** — no ESLint, Prettier, Ruff, Black configured
5. **`uploads/` is gitignored** — uploaded files won't be committed
6. **Python 3.14** venv — use `python3.14` or whatever created the existing venv
7. **Frontend dev server proxies** `/api` and `/uploads` to backend at `localhost:8000`
