"""Mock data seed script for development."""

import asyncio
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.user import User
from app.config import get_settings

settings = get_settings()


async def seed_data():
    """Seed the database with mock data."""
    engine = create_async_engine(settings.database_url, echo=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        # Create admin user
        admin = User(
            username="admin@tiktok-ops.com",
            hashed_password="$2b$12$dummy_hash_replace_on_first_run",
            nickname="Admin",
            role="admin",
            is_active=True,
        )
        session.add(admin)

        # Create operator user
        operator = User(
            username="operator@tiktok-ops.com",
            hashed_password="$2b$12$dummy_hash_replace_on_first_run",
            nickname="运营人员",
            role="operator",
            is_active=True,
        )
        session.add(operator)

        await session.commit()
        print(f"Seeded admin user: {admin.username}")
        print(f"Seeded operator user: {operator.username}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
