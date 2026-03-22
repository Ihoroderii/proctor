# Proctor — Real-time proctoring system

Live streaming (webcam + optional screen), real-time AI-style flag events, proctor dashboard, and recording + review. Built with **LiveKit** for media and **Python (FastAPI)** for the backend.

## Architecture

- **Frontend (React + Vite)**: Candidate app (join → exam → finish) and Proctor app (login → session watch → review). Both use LiveKit for video and your backend for auth and events.
- **Backend (FastAPI)**: Session creation, LiveKit token issuance, WebSocket for real-time events, rules engine (e.g. face missing 10s → flag), recording hooks, and JSON report export.
- **Database**: PostgreSQL (sessions, events, flags, recordings, notes).
- **Media**: LiveKit server (cloud or self-hosted). Candidates publish camera/mic/screen; proctors subscribe.
- **Automated proctor agent** (optional): A Python process that joins the same LiveKit room, subscribes to the candidate’s camera, runs **face detection** (OpenCV), and POSTs `face_detected` / `face_missing` to the backend so the rules engine can flag “no person in frame” without a human watching.

## Quick start

### 1. Backend

```bash
cd backend
cp .env.example .env
# Edit .env: set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET (and optionally DB, S3, Redis)
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
# Create an exam and proctor (see Seed data below)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — candidate: **Join** (exam code + name) → **Exam** (LiveKit + events) → **Finish**. Proctor: **/proctor/login** → **Sessions** → **Watch** / **Review**.

### 3. Database (optional Docker)

```bash
docker compose up -d postgres
# Then run backend; tables are created on startup.
```

### 4. LiveKit

Use [LiveKit Cloud](https://cloud.livekit.io) or self-host. Put the project URL and API key/secret in backend `.env`. The app issues tokens; LiveKit handles WebRTC and (optionally) egress/recording.

## API overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/session/join` | Candidate join by exam code → `session_id` + LiveKit token |
| `POST /api/session/create` | Create session by `exam_id` |
| `POST /api/token/candidate` | LiveKit token for candidate |
| `POST /api/token/proctor` | LiveKit token for proctor |
| `POST /api/proctor/login` | Proctor login → JWT |
| `GET /api/proctor/sessions` | List sessions (proctor JWT) |
| `GET /api/proctor/sessions/:id` | Session detail |
| `GET /api/proctor/sessions/:id/report` | JSON report (events, flags, notes, recordings) |
| `POST /api/token/agent` | LiveKit token for the automated proctor agent |
| `POST /api/internal/agent-event` | Agent posts events (e.g. `face_detected`, `face_missing`); requires `X-Agent-Secret` |
| `WS /ws/session/:id?role=candidate|proctor` | Real-time events; candidate sends, proctor receives + can send actions |

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

Low-level events from the candidate (e.g. `face_missing`, `tab_visibility`) are stored and evaluated:

- Face missing **10s** → medium flag; **30s** → high flag.
- Tab hidden **15s** → medium flag.

Flags are persisted and broadcast to proctors over WebSocket. Proctors can **Warn**, **Pause**, **Terminate**, and **Add note** (API and UI hooks are in place).

## Automated proctor agent (no human needed)

The **proctor agent** joins the exam room as a hidden participant, subscribes to the candidate’s camera track, runs **face detection** (OpenCV Haar cascade) on sampled frames, and POSTs `face_detected` or `face_missing` to your backend. The same rules engine then raises flags (e.g. face missing 10s → warning; 30s → high).

1. **Backend**: Set `AGENT_SECRET` in `.env` (same value the agent will send).
2. **Run one agent per session** (start it when a candidate joins, or run a worker that starts an agent per active room):

```bash
cd agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python proctor_agent.py --session-id 1 --backend-url http://localhost:8000 --agent-secret "your-agent-secret"
```

Use the same `AGENT_SECRET` as in backend `.env`. The agent fetches a LiveKit token from `POST /api/token/agent`, connects to the room, and starts analyzing the first remote video track. It posts events to `POST /api/internal/agent-event` with header `X-Agent-Secret`. You can run the agent automatically when a session is created (e.g. from your backend or a small orchestrator).

## Recording

Recording is prepared in the backend (LiveKit egress). Configure LiveKit egress (e.g. to S3/R2/MinIO) and optionally call `start_room_recording` when a session starts; use LiveKit webhooks or your pipeline to update the `Recording` row with the final file URL. The **Review** page shows recording links from the report.

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
├── agent/
│   ├── proctor_agent.py  # LiveKit room + OpenCV face detection → POST events
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/        # candidate + proctor pages
│   │   └── api.ts
│   └── package.json
├── docker-compose.yml
└── README.md
```

## License

MIT.
