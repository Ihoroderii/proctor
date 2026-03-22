"""Internal API: proctor agent posts face_detected / face_missing events."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import Response

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import ProctorEvent, ProctorFlag, ProctorEventType
from app.schemas.session import AgentEventRequest
from app.services.auth_service import get_session_by_id
from app.websocket.manager import broadcast_to_proctors, get_rules_state
from app.services.rules_engine import evaluate_rules

router = APIRouter(prefix="/api/internal", tags=["internal"])


def verify_agent_secret(x_agent_secret: str | None = Header(None, alias="X-Agent-Secret")):
    settings = get_settings()
    if not settings.agent_secret or x_agent_secret != settings.agent_secret:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Agent-Secret")
    return x_agent_secret


@router.post("/agent-event")
async def agent_event(
    body: AgentEventRequest,
    _: str = Depends(verify_agent_secret),
):
    """
    Proctor agent sends events (e.g. face_detected, face_missing).
    Creates ProctorEvent with source=agent, runs rules engine, broadcasts to proctors.
    """
    session_id = body.session_id
    event_type = body.event_type
    payload = body.payload

    try:
        typ = ProctorEventType(event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown event_type: {event_type}")

    async with AsyncSessionLocal() as db:
        session = await get_session_by_id(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        ev = ProctorEvent(
            session_id=session_id,
            event_type=typ,
            payload=payload or {},
            source="agent",
        )
        db.add(ev)
        await db.commit()
        await db.refresh(ev)

    at = datetime.now(timezone.utc)
    state = get_rules_state(session_id)
    for rule_id, severity, message in evaluate_rules(state, typ, payload, at):
        async with AsyncSessionLocal() as db:
            flag = ProctorFlag(
                session_id=session_id,
                severity=severity,
                rule_id=rule_id,
                message=message,
                payload=payload,
            )
            db.add(flag)
            await db.commit()
        await broadcast_to_proctors(session_id, {
            "type": "flag",
            "flag": {
                "rule_id": rule_id,
                "severity": severity.value,
                "message": message,
                "raised_at": at.isoformat(),
            },
        })

    await broadcast_to_proctors(session_id, {
        "type": "event",
        "event": {"event_type": event_type, "payload": payload or {}, "source": "agent"},
    })
    return Response(status_code=204)
