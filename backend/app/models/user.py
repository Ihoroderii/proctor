from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class Proctor(Base):
    __tablename__ = "proctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    notes = relationship("ProctorNote", back_populates="proctor")
