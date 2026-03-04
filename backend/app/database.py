"""
Async SQLAlchemy engine + FastAPI session dependency.

Railway's DATABASE_URL is postgres://... — asyncpg needs postgresql+asyncpg://
The rewrite here handles both forms so you don't get surprised in prod.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from .config import settings


def _async_url(url: str) -> str:
    """Rewrite Railway's postgres:// or postgresql:// for asyncpg."""
    return url.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
        "postgres://", "postgresql+asyncpg://", 1
    )


engine = create_async_engine(
    _async_url(settings.database_public_url),
    echo=(settings.environment == "development"),
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def create_db_and_tables() -> None:
    """Called at startup. Alembic owns schema in prod; this covers local dev."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)