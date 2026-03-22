"""WebSocket connection manager: broadcast events to proctors, WebRTC signaling candidate<->proctors."""
import asyncio
import json
from typing import AsyncGenerator
from fastapi import WebSocket

# session_id -> set of proctor WebSockets
_proctor_connections: dict[int, set[WebSocket]] = {}
# session_id -> single candidate WebSocket (one candidate per session)
_candidate_connections: dict[int, WebSocket] = {}
# session_id -> rules engine state
_rules_state: dict[int, "SessionSignalState"] = {}
_lock = asyncio.Lock()


def _get_state(session_id: int) -> "SessionSignalState":
    from app.services.rules_engine import SessionSignalState
    if session_id not in _rules_state:
        _rules_state[session_id] = SessionSignalState()
    return _rules_state[session_id]


async def register_proctor(session_id: int, ws: WebSocket) -> None:
    async with _lock:
        if session_id not in _proctor_connections:
            _proctor_connections[session_id] = set()
        _proctor_connections[session_id].add(ws)


async def unregister_proctor(session_id: int, ws: WebSocket) -> None:
    async with _lock:
        if session_id in _proctor_connections:
            _proctor_connections[session_id].discard(ws)
            if not _proctor_connections[session_id]:
                del _proctor_connections[session_id]


async def register_candidate(session_id: int, ws: WebSocket) -> None:
    async with _lock:
        _candidate_connections[session_id] = ws


async def unregister_candidate(session_id: int) -> None:
    async with _lock:
        _candidate_connections.pop(session_id, None)


async def send_to_candidate(session_id: int, message: dict) -> None:
    async with _lock:
        ws = _candidate_connections.get(session_id)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            async with _lock:
                _candidate_connections.pop(session_id, None)


async def broadcast_to_proctors(session_id: int, message: dict) -> None:
    async with _lock:
        connections = _proctor_connections.get(session_id, set())
    dead = set()
    for ws in connections:
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    if dead:
        async with _lock:
            for ws in dead:
                if session_id in _proctor_connections:
                    _proctor_connections[session_id].discard(ws)


def get_rules_state(session_id: int) -> "SessionSignalState":
    return _get_state(session_id)
