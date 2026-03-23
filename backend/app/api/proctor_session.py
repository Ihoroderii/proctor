"""Proctor: list sessions, session detail, actions (warn, pause, terminate), report."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.database import get_db
from app.api.deps import require_proctor
from app.models import ExamSession, Proctor, ProctorEvent, ProctorFlag, Recording, ProctorNote, Exam
from app.models.session import SessionStatus
from app.services.reporting_service import export_report_json

router = APIRouter(prefix="/api/proctor", tags=["proctor"])


@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    proctor: Proctor = Depends(require_proctor),
    status: SessionStatus | None = Query(None),
    limit: int = Query(50, le=100),
):
    q = select(ExamSession).order_by(ExamSession.created_at.desc()).limit(limit)
    if status:
        q = q.where(ExamSession.status == status)
    result = await db.execute(q)
    sessions = result.scalars().all()
    # Load exam for each
    out = []
    for s in sessions:
        exam = (await db.execute(select(Exam).where(Exam.id == s.exam_id))).scalar_one_or_none()
        out.append({
            "id": s.id,
            "room_name": s.room_name,
            "exam_id": s.exam_id,
            "exam_title": exam.title if exam else None,
            "exam_code": exam.code if exam else None,
            "candidate_identifier": s.candidate_identifier,
            "status": s.status.value,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return {"sessions": out}


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    proctor: Proctor = Depends(require_proctor),
):
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    exam = (await db.execute(select(Exam).where(Exam.id == session.exam_id))).scalar_one_or_none()
    return {
        "id": session.id,
        "room_name": session.room_name,
        "exam_id": session.exam_id,
        "exam_title": exam.title if exam else None,
        "exam_code": exam.code if exam else None,
        "candidate_identifier": session.candidate_identifier,
        "status": session.status.value,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


@router.post("/sessions/{session_id}/start")
async def start_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    proctor: Proctor = Depends(require_proctor),
):
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = SessionStatus.in_progress
    session.started_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": session.status.value}


@router.post("/sessions/{session_id}/pause")
async def pause_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    proctor: Proctor = Depends(require_proctor),
):
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = SessionStatus.paused
    await db.commit()
    return {"status": session.status.value}


@router.post("/sessions/{session_id}/terminate")
async def terminate_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    proctor: Proctor = Depends(require_proctor),
):
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = SessionStatus.terminated
    session.ended_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": session.status.value}


class AddNoteBody(BaseModel):
    note: str
    timestamp_sec: int | None = None


@router.post("/sessions/{session_id}/notes")
async def add_note(
    session_id: int,
    body: AddNoteBody,
    db: AsyncSession = Depends(get_db),
    proctor: Proctor = Depends(require_proctor),
):
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    n = ProctorNote(session_id=session_id, proctor_id=proctor.id, note=body.note, timestamp_sec=body.timestamp_sec)
    db.add(n)
    await db.commit()
    return {"id": n.id}


@router.get("/sessions/{session_id}/report")
async def get_report(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    proctor: Proctor = Depends(require_proctor),
):
    data = await export_report_json(db, session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data
