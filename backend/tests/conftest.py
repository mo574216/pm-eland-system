"""Shared backend test fixtures."""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def application() -> FastAPI:
    """Return an isolated app without configured external dependencies."""
    return create_app(
        Settings(
            database_url=None,
            auth_cookie_secure=True,
            auth_cookie_name="__Host-pm_refresh",
        )
    )


@pytest.fixture
def client(application: FastAPI) -> Iterator[TestClient]:
    """Run application lifespan for each API test."""
    with TestClient(application) as test_client:
        yield test_client
