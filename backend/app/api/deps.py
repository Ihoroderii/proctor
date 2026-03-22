"""Dependencies for API routes."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import verify_proctor_token
from app.models import Proctor

security = HTTPBearer(auto_error=False)


async def get_current_proctor(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Proctor | None:
    if not credentials:
        return None
    payload = verify_proctor_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    from sqlalchemy import select
    result = await db.execute(select(Proctor).where(Proctor.id == int(payload["sub"]), Proctor.is_active == True))
    return result.scalar_one_or_none()


def require_proctor(proctor: Proctor | None = Depends(get_current_proctor)) -> Proctor:
    if not proctor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Proctor authentication required")
    return proctor
