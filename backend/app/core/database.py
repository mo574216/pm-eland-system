"""SQLAlchemy engine, session, and readiness infrastructure."""

from collections.abc import AsyncIterator
from typing import cast

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for stable platform persistence models."""


SessionFactory = async_sessionmaker[AsyncSession]


def to_async_database_url(database_url: str) -> str:
    """Normalize a PostgreSQL URL to the approved psycopg async dialect."""
    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    raise ValueError("DATABASE_URL must use the PostgreSQL psycopg dialect.")


def to_sync_database_url(database_url: str) -> str:
    """Return the psycopg SQLAlchemy URL used by synchronous Alembic migrations."""
    return to_async_database_url(database_url)


def create_database_engine(
    database_url: str,
    *,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    connect_timeout_seconds: int = 5,
) -> AsyncEngine:
    """Create the process-level async engine without opening a connection."""
    return create_async_engine(
        to_async_database_url(database_url),
        echo=echo,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        connect_args={"connect_timeout": connect_timeout_seconds},
    )


def create_session_factory(engine: AsyncEngine) -> SessionFactory:
    """Create request/job-scoped sessions with no implicit commit or expiration."""
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def check_database_connection(engine: AsyncEngine) -> bool:
    """Return whether PostgreSQL accepts a trivial query without leaking error details."""
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            return cast(int, result.scalar_one()) == 1
    except Exception:
        return False


async def get_database_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield one session for the request; services own commit and rollback decisions."""
    session_factory: SessionFactory | None = request.app.state.session_factory
    if session_factory is None:
        raise RuntimeError("Database session factory is not configured.")
    async with session_factory() as session:
        yield session
