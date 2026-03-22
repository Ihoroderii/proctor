"""Reporting: export JSON/PDF with attempts, flags, notes, recording links."""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExamSession, ProctorEvent, ProctorFlag, Recording, ProctorNote, Exam


async def get_session_report_data(db: AsyncSession, session_id: int) -> dict:
    """Load session with exam, events, flags, recordings, notes."""
    session_result = await db.execute(
        select(ExamSession)
        .where(ExamSession.id == session_id)
        .options(
            *[getattr(ExamSession, r) for r in ("exam", "events", "flags", "recordings", "notes")]
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        return None
    # Manual load of relations if not eager loaded
    exam = (await db.execute(select(Exam).where(Exam.id == session.exam_id))).scalar_one_or_none()
    events = (await db.execute(select(ProctorEvent).where(ProctorEvent.session_id == session_id).order_by(ProctorEvent.created_at))).scalars().all()
    flags = (await db.execute(select(ProctorFlag).where(ProctorFlag.session_id == session_id).order_by(ProctorFlag.raised_at))).scalars().all()
    recordings = (await db.execute(select(Recording).where(Recording.session_id == session_id))).scalars().all()
    notes = (await db.execute(select(ProctorNote).where(ProctorNote.session_id == session_id).order_by(ProctorNote.created_at))).scalars().all()

    return {
        "session_id": session.id,
        "exam_id": session.exam_id,
        "exam_title": exam.title if exam else None,
        "exam_code": exam.code if exam else None,
        "candidate_identifier": session.candidate_identifier,
        "status": session.status.value,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "events": [
            {
                "event_type": e.event_type.value,
                "source": e.source,
                "payload": e.payload,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
        "flags": [
            {
                "severity": f.severity.value,
                "rule_id": f.rule_id,
                "message": f.message,
                "raised_at": f.raised_at.isoformat() if f.raised_at else None,
            }
            for f in flags
        ],
        "recordings": [
            {"id": r.id, "file_url": r.file_url, "kind": r.kind}
            for r in recordings
        ],
        "proctor_notes": [
            {"note": n.note, "timestamp_sec": n.timestamp_sec, "created_at": n.created_at.isoformat() if n.created_at else None}
            for n in notes
        ],
    }


async def export_report_json(db: AsyncSession, session_id: int) -> dict | None:
    """Export report as JSON-serializable dict."""
    return await get_session_report_data(db, session_id)
