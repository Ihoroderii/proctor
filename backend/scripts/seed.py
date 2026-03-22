#!/usr/bin/env python3
"""Create tables and seed an exam + proctor for local testing."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine, Base, AsyncSessionLocal
from app.models import Exam, Proctor
from app.services.auth_service import hash_password


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        r = await db.execute(select(Exam).where(Exam.code == "DEMO"))
        if r.scalar_one_or_none():
            print("DEMO exam already exists")
        else:
            db.add(Exam(code="DEMO", title="Demo Exam", duration_minutes=60))
            print("Created exam DEMO")
        r = await db.execute(select(Proctor).where(Proctor.email == "proctor@test.com"))
        if r.scalar_one_or_none():
            print("Proctor proctor@test.com already exists")
        else:
            db.add(Proctor(email="proctor@test.com", hashed_password=hash_password("proctor123")))
            print("Created proctor proctor@test.com / proctor123")
        await db.commit()
    await engine.dispose()
    print("Done. Use exam code DEMO to join; proctor login: proctor@test.com / proctor123")


if __name__ == "__main__":
    asyncio.run(main())
