from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class Recording(Base):
    __tablename__ = "recordings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id"), nullable=False)
    egress_id: Mapped[str] = mapped_column(String(128), nullable=True)  # external recording ID
    kind: Mapped[str] = mapped_column(String(32), nullable=False)  # "room_composite" | "track"
    file_url: Mapped[str] = mapped_column(Text, nullable=True)  # S3/R2 URL when ready
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    session = relationship("ExamSession", back_populates="recordings")
