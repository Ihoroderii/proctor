"""Recording: create Recording rows and store URLs (S3/R2/MinIO)."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Recording

settings = get_settings()


async def create_recording_row(db: AsyncSession, session_id: int, egress_id: str | None = None) -> Recording:
    """Create a Recording record."""
    rec = Recording(
        session_id=session_id,
        egress_id=egress_id,
        kind="room_composite",
    )
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    return rec


async def set_recording_file_url(db: AsyncSession, recording_id: int, file_url: str) -> None:
    """Update recording with final file URL."""
    from sqlalchemy import update
    from app.models import Recording
    await db.execute(update(Recording).where(Recording.id == recording_id).values(file_url=file_url, ended_at=datetime.utcnow()))
    return rec
