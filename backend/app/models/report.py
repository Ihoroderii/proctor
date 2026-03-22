from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class ProctorNote(Base):
    __tablename__ = "proctor_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id"), nullable=False)
    proctor_id: Mapped[int] = mapped_column(ForeignKey("proctors.id"), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp_sec: Mapped[int] = mapped_column(Integer, nullable=True)  # position in recording
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("ExamSession", back_populates="notes")
    proctor = relationship("Proctor", back_populates="notes")
