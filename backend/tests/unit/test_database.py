"""Database infrastructure unit tests."""

from typing import Any, cast

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.database import (
    check_database_connection,
    create_database_engine,
    to_async_database_url,
    to_sync_database_url,
)


def test_postgresql_url_is_normalized_to_psycopg() -> None:
    plain_url = "postgresql://user:password@localhost/database"

    assert to_async_database_url(plain_url) == (
        "postgresql+psycopg://user:password@localhost/database"
    )
    assert to_sync_database_url(plain_url) == (
        "postgresql+psycopg://user:password@localhost/database"
    )


def test_non_postgresql_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="PostgreSQL psycopg"):
        to_async_database_url("sqlite:///local.db")


@pytest.mark.asyncio
async def test_engine_uses_approved_driver_without_connecting() -> None:
    engine = create_database_engine("postgresql://user:password@localhost/database")
    try:
        assert engine.url.drivername == "postgresql+psycopg"
        assert engine.pool._pre_ping is True
    finally:
        await engine.dispose()


class SuccessfulResult:
    def scalar_one(self) -> int:
        return 1


class SuccessfulConnection:
    async def execute(self, _: Any) -> SuccessfulResult:
        return SuccessfulResult()


class SuccessfulConnectionContext:
    async def __aenter__(self) -> SuccessfulConnection:
        return SuccessfulConnection()

    async def __aexit__(self, *_: object) -> None:
        return None


class SuccessfulEngine:
    def connect(self) -> SuccessfulConnectionContext:
        return SuccessfulConnectionContext()


class FailingConnectionContext:
    async def __aenter__(self) -> None:
        raise ConnectionError("database unavailable")

    async def __aexit__(self, *_: object) -> None:
        return None


class FailingEngine:
    def connect(self) -> FailingConnectionContext:
        return FailingConnectionContext()


@pytest.mark.asyncio
async def test_database_probe_reports_success() -> None:
    engine = cast(AsyncEngine, SuccessfulEngine())
    assert await check_database_connection(engine) is True


@pytest.mark.asyncio
async def test_database_probe_safely_reports_failure() -> None:
    engine = cast(AsyncEngine, FailingEngine())
    assert await check_database_connection(engine) is False
