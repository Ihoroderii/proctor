"""Rules engine: turn low-level signals into flags (e.g. face missing 10s = warning)."""
from datetime import datetime, timezone
from dataclasses import dataclass, field

from app.models.events import ProctorEventType, FlagSeverity


@dataclass
class SessionSignalState:
    """Per-session state for rule evaluation."""
    face_last_seen: datetime | None = None
    face_missing_since: datetime | None = None
    last_tab_visible: datetime | None = None
    tab_hidden_since: datetime | None = None


# Rule config: (rule_id, severity, threshold_seconds)
FACE_MISSING_WARNING_SEC = 10
FACE_MISSING_MAJOR_SEC = 30
TAB_HIDDEN_WARNING_SEC = 15


def evaluate_face_rule(
    state: SessionSignalState,
    event_type: ProctorEventType,
    at: datetime,
) -> list[tuple[str, FlagSeverity, str]]:
    """Returns list of (rule_id, severity, message) to raise."""
    flags = []
    if event_type == ProctorEventType.face_detected:
        state.face_last_seen = at
        state.face_missing_since = None
    elif event_type == ProctorEventType.face_missing:
        if state.face_missing_since is None:
            state.face_missing_since = at
        elapsed = (at - state.face_missing_since).total_seconds()
        if elapsed >= FACE_MISSING_MAJOR_SEC:
            flags.append(("face_missing_30s", FlagSeverity.high, "Face not detected for 30+ seconds"))
        elif elapsed >= FACE_MISSING_WARNING_SEC:
            flags.append(("face_missing_10s", FlagSeverity.medium, "Face not detected for 10+ seconds"))
    return flags


def evaluate_tab_visibility_rule(
    state: SessionSignalState,
    event_type: ProctorEventType,
    payload: dict | None,
    at: datetime,
) -> list[tuple[str, FlagSeverity, str]]:
    flags = []
    if event_type == ProctorEventType.tab_visibility and payload:
        visible = payload.get("visible", True)
        if visible:
            state.tab_hidden_since = None
        else:
            if state.tab_hidden_since is None:
                state.tab_hidden_since = at
            elapsed = (at - state.tab_hidden_since).total_seconds()
            if elapsed >= TAB_HIDDEN_WARNING_SEC:
                flags.append(("tab_hidden_15s", FlagSeverity.medium, "Tab hidden for 15+ seconds"))
    return flags


def evaluate_rules(
    state: SessionSignalState,
    event_type: ProctorEventType,
    payload: dict | None,
    at: datetime | None = None,
) -> list[tuple[str, FlagSeverity, str]]:
    at = at or datetime.now(timezone.utc)
    all_flags = []
    all_flags.extend(evaluate_face_rule(state, event_type, at))
    all_flags.extend(evaluate_tab_visibility_rule(state, event_type, payload, at))
    return all_flags
