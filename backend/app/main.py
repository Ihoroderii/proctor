"""Proctor backend — FastAPI app."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.api import session as session_api
from app.api import proctor_auth
from app.api import proctor_session
from app.api import ws
from app.api import agent_event as agent_event_api

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables (in production use Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="Real-time proctoring: browser-based face/voice/phone detection, WebRTC media, events, flags, reporting.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session_api.router)
app.include_router(proctor_auth.router)
app.include_router(proctor_session.router)
app.include_router(ws.router)
app.include_router(agent_event_api.router)


@app.get("/health")
def health():
    return {"status": "ok"}
