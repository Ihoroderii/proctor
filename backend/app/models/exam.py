from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    sessions = relationship("ExamSession", back_populates="exam")
