"""Proctor login and auth."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.proctor import ProctorLoginRequest, ProctorLoginResponse
from app.services.auth_service import (
    get_proctor_by_email,
    verify_password,
    create_proctor_access_token,
)

router = APIRouter(prefix="/api/proctor", tags=["proctor"])


@router.post("/login", response_model=ProctorLoginResponse)
async def proctor_login(
    body: ProctorLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    proctor = await get_proctor_by_email(db, body.email)
    if not proctor or not verify_password(body.password, proctor.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_proctor_access_token(proctor.id, proctor.email)
    return ProctorLoginResponse(
        access_token=token,
        token_type="bearer",
        proctor_id=proctor.id,
        email=proctor.email,
    )
