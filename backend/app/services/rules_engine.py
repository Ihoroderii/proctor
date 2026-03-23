"""Rules engine: turn low-level browser signals into flags."""
from datetime import datetime, timezone
from dataclasses import dataclass, field

from app.models.events import ProctorEventType, FlagSeverity


@dataclass
class SessionSignalState:
    """Per-session state for rule evaluation."""
    # Face
    face_last_seen: datetime | None = None
    face_missing_since: datetime | None = None
    multiple_faces_since: datetime | None = None
    # Tab / Window / Fullscreen
    last_tab_visible: datetime | None = None
    tab_hidden_since: datetime | None = None
    fullscreen_exited_since: datetime | None = None
    window_blurred_since: datetime | None = None
    # Phone
    phone_detected_since: datetime | None = None
    # Voice
    voice_detected_since: datetime | None = None


# Thresholds (seconds)
FACE_MISSING_WARNING_SEC = 10
FACE_MISSING_MAJOR_SEC = 30
MULTIPLE_FACES_SEC = 5
TAB_HIDDEN_WARNING_SEC = 5
TAB_HIDDEN_MAJOR_SEC = 15
FULLSCREEN_EXIT_SEC = 3
WINDOW_BLUR_SEC = 5
PHONE_IMMEDIATE = True  # phone = instant flag
VOICE_SUSTAINED_SEC = 10


def evaluate_face_rule(
    state: SessionSignalState,
    event_type: ProctorEventType,
    at: datetime,
) -> list[tuple[str, FlagSeverity, str]]:
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
    elif event_type == ProctorEventType.multiple_faces:
        if state.multiple_faces_since is None:
            state.multiple_faces_since = at
        elapsed = (at - state.multiple_faces_since).total_seconds()
        if elapsed >= MULTIPLE_FACES_SEC:
            flags.append(("multiple_faces", FlagSeverity.high, "Multiple faces detected for 5+ seconds"))
    else:
        state.multiple_faces_since = None
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
            if elapsed >= TAB_HIDDEN_MAJOR_SEC:
                flags.append(("tab_hidden_15s", FlagSeverity.high, "Tab hidden for 15+ seconds"))
            elif elapsed >= TAB_HIDDEN_WARNING_SEC:
                flags.append(("tab_hidden_5s", FlagSeverity.medium, "Tab hidden for 5+ seconds"))
    return flags


def evaluate_fullscreen_rule(
    state: SessionSignalState,
    event_type: ProctorEventType,
    at: datetime,
) -> list[tuple[str, FlagSeverity, str]]:
    flags = []
    if event_type == ProctorEventType.fullscreen_exit:
        if state.fullscreen_exited_since is None:
            state.fullscreen_exited_since = at
        elapsed = (at - state.fullscreen_exited_since).total_seconds()
        if elapsed >= FULLSCREEN_EXIT_SEC:
            flags.append(("fullscreen_exit", FlagSeverity.medium, "Candidate exited fullscreen"))
    elif event_type == ProctorEventType.fullscreen_enter:
        state.fullscreen_exited_since = None
    return flags


def evaluate_window_blur_rule(
    state: SessionSignalState,
    event_type: ProctorEventType,
    at: datetime,
) -> list[tuple[str, FlagSeverity, str]]:
    flags = []
    if event_type == ProctorEventType.window_blur:
        if state.window_blurred_since is None:
            state.window_blurred_since = at
        elapsed = (at - state.window_blurred_since).total_seconds()
        if elapsed >= WINDOW_BLUR_SEC:
            flags.append(("window_blur_5s", FlagSeverity.medium, "Browser window lost focus for 5+ seconds"))
    elif event_type == ProctorEventType.window_focus:
        state.window_blurred_since = None
    return flags


def evaluate_phone_rule(
    state: SessionSignalState,
    event_type: ProctorEventType,
    at: datetime,
) -> list[tuple[str, FlagSeverity, str]]:
    flags = []
    if event_type == ProctorEventType.phone_detected:
        flags.append(("phone_detected", FlagSeverity.high, "Phone or mobile device detected on camera"))
        state.phone_detected_since = at
    elif event_type == ProctorEventType.phone_gone:
        state.phone_detected_since = None
    return flags


def evaluate_voice_rule(
    state: SessionSignalState,
    event_type: ProctorEventType,
    at: datetime,
) -> list[tuple[str, FlagSeverity, str]]:
    flags = []
    if event_type == ProctorEventType.voice_detected:
        if state.voice_detected_since is None:
            state.voice_detected_since = at
        elapsed = (at - state.voice_detected_since).total_seconds()
        if elapsed >= VOICE_SUSTAINED_SEC:
            flags.append(("voice_sustained", FlagSeverity.medium, "Sustained voice/talking detected for 10+ seconds"))
    elif event_type == ProctorEventType.voice_silent:
        state.voice_detected_since = None
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
    all_flags.extend(evaluate_fullscreen_rule(state, event_type, at))
    all_flags.extend(evaluate_window_blur_rule(state, event_type, at))
    all_flags.extend(evaluate_phone_rule(state, event_type, at))
    all_flags.extend(evaluate_voice_rule(state, event_type, at))
    return all_flags
