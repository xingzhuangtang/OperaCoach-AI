# OperaCoach-AI V2 (MVP)

## Project Overview
A minimal viable product for opera singing coaching, focusing on:
- Video/Audio upload and playback
- Video to Audio extraction
- AI-based audio slicing (by lyrics/melody)
- Visual display of slices (time, lyrics, commands)

## Architecture
- **Frontend**: Vue 3 + TypeScript + Element Plus (Dreamy UI Style)
- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL
- **AI Service**: OpenAI Whisper + Librosa (embedded in Backend)

## Quick Start

### 1. Environment Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Run Services
```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

## Directory Structure
```
opera-coach-ai/
├── backend/          # FastAPI Application
├── frontend/         # Vue 3 Application
├── docker-compose.yml
└── docs/             # Design docs and plans
```
