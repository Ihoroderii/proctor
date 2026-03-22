from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from app.database import Base


class SessionStatus(str, enum.Enum):
    created = "created"
    joined = "joined"      # candidate joined room
    in_progress = "in_progress"
    paused = "paused"
    terminated = "terminated"
    finished = "finished"


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), nullable=False)
    candidate_identifier: Mapped[str] = mapped_column(String(256), nullable=True)  # name or ID
    livekit_room_name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus), default=SessionStatus.created, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    exam = relationship("Exam", back_populates="sessions")
    events = relationship("ProctorEvent", back_populates="session", order_by="ProctorEvent.created_at")
    flags = relationship("ProctorFlag", back_populates="session", order_by="ProctorFlag.raised_at")
    recordings = relationship("Recording", back_populates="session")
    notes = relationship("ProctorNote", back_populates="session")
