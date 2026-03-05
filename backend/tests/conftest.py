"""
tests/conftest.py

Shared fixtures for all integration tests.
Uses an in-memory SQLite DB (via aiosqlite) so tests never touch your real Postgres.

Install deps if you haven't:
    pip install pytest-asyncio httpx aiosqlite

Run all tests:
    pytest tests/ -v
"""

import os

# Stub required env vars before app/config.py is imported.
# pydantic-settings validates Settings() at module load time, so these must
# be set before `from app.main import app` runs.
os.environ.setdefault("DATABASE_PUBLIC_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-in-unit-tests")

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.database import get_session
from app.models import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    AsyncTestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncTestSession() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def seeded_user(db_session):
    user = User(auth_token="test-token")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def client(db_session, seeded_user):
    # seeded_user must be created before the client starts making requests,
    # so get_current_user (which grabs first User row) finds it.
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
