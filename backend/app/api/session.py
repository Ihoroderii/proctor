"""Session creation and join endpoints. Media uses WebRTC + WebSocket signaling."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.session import (
    SessionCreateRequest,
    SessionCreateResponse,
    JoinRequest,
    JoinResponse,
)
from app.services.auth_service import (
    create_exam_session,
    get_exam_by_code,
)

router = APIRouter(prefix="/api", tags=["session"])


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
        room_name=session.room_name,
    )


@router.post("/session/join", response_model=JoinResponse)
async def join_exam(
    body: JoinRequest,
    db: AsyncSession = Depends(get_db),
):
    """Candidate join: create session by exam code. Returns session_id and room name."""
    exam = await get_exam_by_code(db, body.exam_code)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    session = await create_exam_session(
        db, exam_id=exam.id, candidate_identifier=body.candidate_identifier
    )
    return JoinResponse(
        session_id=session.id,
        room_name=session.room_name,
    )
