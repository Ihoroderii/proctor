from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from app.database import Base


class ProctorEventType(str, enum.Enum):
    # Face detection (browser-based)
    face_detected = "face_detected"
    face_missing = "face_missing"
    multiple_faces = "multiple_faces"
    # Object detection
    phone_detected = "phone_detected"
    phone_gone = "phone_gone"
    # Voice / audio
    voice_detected = "voice_detected"
    voice_silent = "voice_silent"
    # Camera & mic status
    camera_off = "camera_off"
    camera_on = "camera_on"
    mic_off = "mic_off"
    mic_on = "mic_on"
    # Browser lockdown
    tab_visibility = "tab_visibility"  # {visible: true/false}
    fullscreen_exit = "fullscreen_exit"
    fullscreen_enter = "fullscreen_enter"
    window_blur = "window_blur"
    window_focus = "window_focus"
    # Screen capture (optional)
    screen_share_start = "screen_share_start"
    screen_share_stop = "screen_share_stop"
    # Proctor actions
    warn = "warn"
    pause = "pause"
    resume = "resume"
    terminate = "terminate"
    note = "note"


class FlagSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ProctorEvent(Base):
    """Raw events from candidate or proctor (stored for timeline)."""
    __tablename__ = "proctor_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id"), nullable=False)
    event_type: Mapped[ProctorEventType] = mapped_column(SQLEnum(ProctorEventType), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=True)  # e.g. {"visible": false}
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # "candidate" | "proctor"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("ExamSession", back_populates="events")


class ProctorFlag(Base):
    """Raised flags from rules engine (face missing 10s = warning, etc.)."""
    __tablename__ = "proctor_flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id"), nullable=False)
    severity: Mapped[FlagSeverity] = mapped_column(SQLEnum(FlagSeverity), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "face_missing_10s"
    message: Mapped[str] = mapped_column(String(512), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    raised_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    session = relationship("ExamSession", back_populates="flags")
