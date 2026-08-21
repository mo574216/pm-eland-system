"""Unit tests for safe test-database provisioning."""

import pytest

from scripts.create_test_database import (
    to_psycopg_connection_string,
    validate_test_database_name,
)


@pytest.mark.parametrize("database_name", ["pm_system_test", "a1_test"])
def test_validate_test_database_name_accepts_safe_test_names(database_name: str) -> None:
    assert validate_test_database_name(database_name) == database_name


@pytest.mark.parametrize(
    "database_name",
    ["production", "PM_SYSTEM_TEST", "pm-system-test", "1_pm_test", 'pm_test"; DROP DATABASE x'],
)
def test_validate_test_database_name_rejects_unsafe_names(database_name: str) -> None:
    with pytest.raises(ValueError, match="Test database name"):
        validate_test_database_name(database_name)


def test_to_psycopg_connection_string_removes_sqlalchemy_driver_marker() -> None:
    assert (
        to_psycopg_connection_string("postgresql+psycopg://user:password@localhost/postgres")
        == "postgresql://user:password@localhost/postgres"
    )


def test_to_psycopg_connection_string_rejects_other_databases() -> None:
    with pytest.raises(ValueError, match="must use PostgreSQL"):
        to_psycopg_connection_string("sqlite:///test.db")
