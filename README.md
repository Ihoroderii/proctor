# Proctor — Browser-based proctoring system

Real-time proctoring with webcam monitoring, face/phone/voice detection, browser lockdown, proctor dashboard, and reporting. All detection runs **in the candidate's browser** using TensorFlow.js — no external media server required. Built with **React + Vite** for the frontend and **Python (FastAPI)** for the backend.

## Architecture

- **Frontend (React + Vite + TensorFlow.js)**: Candidate app (join → exam → finish) and Proctor app (login → session watch → review). Candidate's browser runs all detection and sends events via WebSocket. Proctor watches a live WebRTC video feed.
- **Backend (FastAPI)**: Session creation, JWT auth, WebSocket relay for real-time events, rules engine (face missing 10s → flag, phone detected → instant flag, etc.), and JSON report export.
- **Database**: PostgreSQL (sessions, events, flags, recordings, notes).
- **WebRTC**: Peer-to-peer video between candidate and proctor via custom WebSocket signaling (STUN: `stun.l.google.com:19302`).
- **Browser detection**: TensorFlow.js BlazeFace (face), COCO-SSD (phone), Web Audio API (voice), Page Visibility / Fullscreen / blur APIs (browser lockdown).

## Quick start

### 1. Backend

```bash
cd backend
cp .env.example .env
# Edit .env: set DATABASE_URL, SECRET_KEY, AGENT_SECRET
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
# Create an exam and proctor (see Seed data below)
# Create an exam and proctor (see Seed data below)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — candidate: **Join** (exam code + name) → **Exam** (live detection + events) → **Finish**. Proctor: **/proctor/login** → **Sessions** → **Watch** / **Review**.

### 3. Database (optional Docker)

```bash
docker compose up -d postgres
# Then run backend; tables are created on startup.
```

## Detection features

All detection runs in the candidate's browser (`frontend/src/lib/proctoring.ts`):

| Feature | Technology | Events |
|---------|-----------|--------|
| Face present/missing | TensorFlow.js BlazeFace | `face_detected`, `face_missing` |
| Multiple faces | BlazeFace (count > 1) | `multiple_faces` |
| Phone detection | TensorFlow.js COCO-SSD | `phone_detected`, `phone_gone` |
| Voice activity | Web Audio API (RMS threshold) | `voice_detected`, `voice_silent` |
| Tab switching | Page Visibility API | `tab_hidden`, `tab_visible` |
| Fullscreen exit | Fullscreen API | `fullscreen_exit`, `fullscreen_enter` |
| Window blur | Window blur/focus events | `window_blur`, `window_focus` |
| Browser lockdown | beforeunload + keyboard shortcut blocking | preventive |

## API overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/session/join` | Candidate join by exam code → `session_id` + `room_name` |
| `POST /api/session/create` | Create session by `exam_id` |
| `POST /api/proctor/login` | Proctor login → JWT |
| `GET /api/proctor/sessions` | List sessions (proctor JWT) |
| `GET /api/proctor/sessions/:id` | Session detail |
| `GET /api/proctor/sessions/:id/report` | JSON report (events, flags, notes) |
| `POST /api/internal/agent-event` | Internal event endpoint; requires `X-Agent-Secret` header |
| `WS /ws/session/:id?role=candidate\|proctor` | Real-time events; candidate sends detection events, proctor receives + can send actions |

## Seed data

Create an exam and a proctor so you can log in and run a session:

```bash
cd backend
source .venv/bin/activate
python -c "
import asyncio
from app.database import AsyncSessionLocal, engine
from app.database import Base
from app.models import Exam, Proctor
from app.services.auth_service import hash_password

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        db.add(Exam(code='DEMO', title='Demo Exam', duration_minutes=60))
        db.add(Proctor(email='proctor@test.com', hashed_password=hash_password('proctor123')))
        await db.commit()
asyncio.run(seed())
print('Exam DEMO and proctor proctor@test.com / proctor123 created')
"
```

Then: **Join** with code `DEMO` and any name; **Proctor login** with `proctor@test.com` / `proctor123`.

## Rules engine

Events from the candidate's browser are stored and evaluated by the rules engine:

| Rule | Threshold | Severity |
|------|-----------|----------|
| Face missing | 10s → medium; 30s → high | Medium / High |
| Multiple faces | 5s sustained | High |
| Tab hidden | 5s → medium; 15s → high | Medium / High |
| Fullscreen exit | 3s | Medium |
| Window blur | 5s | Medium |
| Phone detected | Instant | High |
| Voice sustained | 10s | Medium |

Flags are persisted and broadcast to proctors over WebSocket. Proctors can **Warn**, **Pause**, **Terminate**, and **Add note**.

## Project layout

## Project layout

```
proctor/
├── backend/
│   ├── app/
│   │   ├── api/          # REST + WebSocket + internal agent-event
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic
│   │   ├── services/     # Auth, rules, recording, reporting
│   │   └── websocket/    # Connection manager
│   ├── requirements.txt
│   └── .env.example
├── agent/                # DEPRECATED — detection moved to browser
├── frontend/
│   ├── src/
│   │   ├── lib/          # proctoring.ts — all browser-based detection
│   │   ├── pages/        # candidate + proctor pages
│   │   └── api.ts
│   └── package.json
├── docker-compose.yml
└── README.md
```

## License

MIT.
