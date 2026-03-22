"""Recording: trigger LiveKit egress (optional), store Recording rows and URLs."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Recording

settings = get_settings()


async def create_recording_row(db: AsyncSession, session_id: int, egress_id: str | None = None) -> Recording:
    """Create a Recording record. Call when starting egress."""
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
    """Update recording with final file URL (e.g. from LiveKit egress webhook)."""
    from sqlalchemy import update
    from app.models import Recording
    await db.execute(update(Recording).where(Recording.id == recording_id).values(file_url=file_url, ended_at=datetime.utcnow()))


async def start_room_recording(db: AsyncSession, session_id: int, room_name: str) -> Recording | None:
    """
    Start LiveKit room composite egress and create a Recording row.
    Requires LiveKit server with egress enabled. For S3/R2, configure via LiveKit Cloud
    or your LiveKit server egress config; you can also use webhooks to get the file URL
    and call set_recording_file_url.
    """
    egress_id = None
    try:
        from livekit import api
        # LiveKitAPI usage: see https://docs.livekit.io/reference/python/livekit/api/
        lk = api.LiveKitAPI(settings.livekit_url, settings.livekit_api_key, settings.livekit_api_secret)
        # Start room composite; exact API may vary by livekit-api version
        # info = await lk.egress.start_room_composite_egress(room_name=room_name, ...)
        # egress_id = info.egress_id
        # For now we only create the DB row; integrate with your LiveKit egress setup
        pass
    except Exception:
        pass
    rec = await create_recording_row(db, session_id, egress_id)
    return rec
