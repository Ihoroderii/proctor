"""WebSocket: /ws/session/{session_id} — candidate sends events, proctors receive."""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.models import ProctorEvent, ProctorFlag, ProctorEventType, FlagSeverity
from app.services.auth_service import get_session_by_id, verify_proctor_token
from app.websocket.manager import (
    register_proctor,
    unregister_proctor,
    register_candidate,
    unregister_candidate,
    broadcast_to_proctors,
    send_to_candidate,
    get_rules_state,
)
from app.services.rules_engine import evaluate_rules

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/session/{session_id}")
async def session_websocket(
    websocket: WebSocket,
    session_id: int,
    role: str = Query(..., description="candidate | proctor"),
    token: str = Query(None, description="Proctor JWT when role=proctor"),
):
    await websocket.accept()
    from app.database import AsyncSessionLocal

    if role == "proctor":
        if not token:
            await websocket.close(code=4001)
            return
        payload = verify_proctor_token(token)
        if not payload:
            await websocket.close(code=4001)
            return
        async with AsyncSessionLocal() as db:
            session = await get_session_by_id(db, session_id)
            if not session:
                await websocket.close(code=4004)
                return
        await register_proctor(session_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    # WebRTC signaling: relay to candidate
                    if msg.get("type") in ("webrtc_answer", "webrtc_ice"):
                        await send_to_candidate(session_id, msg)
                        continue
                    action = msg.get("action")
                    if action in ("warn", "pause", "resume", "terminate", "note"):
                        async with AsyncSessionLocal() as db:
                            ev = ProctorEvent(
                                session_id=session_id,
                                event_type=ProctorEventType(action),
                                payload=msg.get("payload"),
                                source="proctor",
                            )
                            db.add(ev)
                            await db.commit()
                        await broadcast_to_proctors(session_id, {"type": "event", "event": msg})
                except json.JSONDecodeError:
                    pass
        except WebSocketDisconnect:
            pass
        finally:
            await unregister_proctor(session_id, websocket)
        return

    if role == "candidate":
        async with AsyncSessionLocal() as db:
            session = await get_session_by_id(db, session_id)
            if not session:
                await websocket.close(code=4004)
                return
        await register_candidate(session_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    # WebRTC signaling: relay to proctors
                    if msg.get("type") in ("webrtc_offer", "webrtc_ice"):
                        await broadcast_to_proctors(session_id, msg)
                        continue
                    event_type_str = msg.get("event_type")
                    payload = msg.get("payload")
                    if not event_type_str:
                        continue
                    try:
                        event_type = ProctorEventType(event_type_str)
                    except ValueError:
                        continue
                    async with AsyncSessionLocal() as db:
                        ev = ProctorEvent(
                            session_id=session_id,
                            event_type=event_type,
                            payload=payload,
                            source="candidate",
                        )
                        db.add(ev)
                        await db.commit()
                        await db.refresh(ev)
                    # Run rules engine
                    state = get_rules_state(session_id)
                    from datetime import datetime, timezone
                    at = datetime.now(timezone.utc)
                    for rule_id, severity, message in evaluate_rules(state, event_type, payload, at):
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
                    await broadcast_to_proctors(session_id, {"type": "event", "event": msg})
                except json.JSONDecodeError:
                    pass
        except WebSocketDisconnect:
            pass
        finally:
            await unregister_candidate(session_id)
        return

    await websocket.close(code=4000)
