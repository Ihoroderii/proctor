"""Session creation and join endpoints. Media uses WebRTC + our WebSocket signaling (no LiveKit)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.session import (
    SessionCreateRequest,
    SessionCreateResponse,
    TokenRequest,
    TokenResponse,
    JoinRequest,
    JoinResponse,
    AgentTokenRequest,
)
from app.services.auth_service import (
    create_exam_session,
    get_session_by_id,
    get_exam_by_code,
)
from app.config import get_settings

router = APIRouter(prefix="/api", tags=["session"])
settings = get_settings()


@router.post("/session/create", response_model=SessionCreateResponse)
async def create_session(
    body: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create exam session (by exam_id). Returns session_id and room name."""
    session = await create_exam_session(
        db, exam_id=body.exam_id, candidate_identifier=body.candidate_identifier
    )
    return SessionCreateResponse(
        session_id=session.id,
        livekit_room_name=session.livekit_room_name,
    )


@router.post("/session/join", response_model=JoinResponse)
async def join_exam(
    body: JoinRequest,
    db: AsyncSession = Depends(get_db),
):
    """Candidate join: create session by exam code. Returns session_id and room name. Media via WebRTC + WebSocket signaling."""
    exam = await get_exam_by_code(db, body.exam_code)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    session = await create_exam_session(
        db, exam_id=exam.id, candidate_identifier=body.candidate_identifier
    )
    return JoinResponse(
        session_id=session.id,
        livekit_room_name=session.livekit_room_name,
        token=None,
        livekit_url=None,
    )


@router.post("/token/candidate", response_model=TokenResponse)
async def token_candidate(
    body: TokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """No LiveKit: returns empty. Candidate uses WebRTC + WebSocket signaling."""
    session = await get_session_by_id(db, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return TokenResponse(token="", livekit_url="")


@router.post("/token/proctor", response_model=TokenResponse)
async def token_proctor(
    body: TokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """No LiveKit: returns empty. Proctor uses WebRTC + WebSocket signaling."""
    session = await get_session_by_id(db, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return TokenResponse(token="", livekit_url="")


@router.post("/token/agent", response_model=TokenResponse)
async def token_agent(
    body: AgentTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """No LiveKit: automated agent not used when using WebRTC-only mode."""
    session = await get_session_by_id(db, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return TokenResponse(token="", livekit_url="")
