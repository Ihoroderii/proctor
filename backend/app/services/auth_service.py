"""Auth: session creation, proctor JWT."""
import secrets
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Exam, ExamSession, Proctor
from app.models.session import SessionStatus

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _room_name(session_id: int) -> str:
    return f"proctor-session-{session_id}"


async def create_exam_session(db: AsyncSession, exam_id: int, candidate_identifier: str | None = None) -> ExamSession:
    """Create a new exam session and return it. Room name is derived from session id."""
    session = ExamSession(
        exam_id=exam_id,
        candidate_identifier=candidate_identifier,
        room_name="",  # set after insert
        status=SessionStatus.created,
    )
    db.add(session)
    await db.flush()
    session.room_name = _room_name(session.id)
    await db.refresh(session)
    return session


async def get_session_by_id(db: AsyncSession, session_id: int) -> ExamSession | None:
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    return result.scalar_one_or_none()


async def get_session_by_room(db: AsyncSession, room_name: str) -> ExamSession | None:
    result = await db.execute(select(ExamSession).where(ExamSession.room_name == room_name))
    return result.scalar_one_or_none()


async def get_exam_by_code(db: AsyncSession, code: str) -> Exam | None:
    result = await db.execute(select(Exam).where(Exam.code == code))
    return result.scalar_one_or_none()


def verify_proctor_token(token: str) -> dict | None:
    """Decode and verify our API JWT for proctor auth. Returns payload or None."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def create_proctor_access_token(proctor_id: int, email: str) -> str:
    """Create JWT for proctor API access."""
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(proctor_id), "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def get_proctor_by_email(db: AsyncSession, email: str) -> Proctor | None:
    result = await db.execute(select(Proctor).where(Proctor.email == email, Proctor.is_active == True))
    return result.scalar_one_or_none()
