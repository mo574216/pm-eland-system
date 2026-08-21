"""Create an isolated PostgreSQL test database when it does not already exist."""

import argparse
import os
import re

import psycopg
from psycopg import sql

DEFAULT_TEST_DATABASE_NAME = "pm_system_test"
TEST_DATABASE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,57}_test$")


def validate_test_database_name(database_name: str) -> str:
    """Reject unsafe or non-test database names before issuing administrative SQL."""
    if not TEST_DATABASE_NAME_PATTERN.fullmatch(database_name):
        raise ValueError(
            "Test database name must use lowercase letters, digits, or underscores, "
            "start with a letter, end with '_test', and be at most 63 characters."
        )
    return database_name


def to_psycopg_connection_string(database_url: str) -> str:
    """Convert the supported SQLAlchemy URL form to a psycopg connection string."""
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    if database_url.startswith("postgresql://"):
        return database_url
    raise ValueError("The admin URL must use PostgreSQL with the psycopg driver.")


def create_test_database(admin_url: str, database_name: str) -> bool:
    """Create the named test database idempotently and return whether it was created."""
    validated_name = validate_test_database_name(database_name)
    connection_string = to_psycopg_connection_string(admin_url)

    with psycopg.connect(connection_string, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (validated_name,))
            if cursor.fetchone() is not None:
                return False
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(validated_name)))
    return True


def main() -> None:
    """Parse command-line configuration and ensure the test database exists."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--admin-url",
        default=os.getenv("TEST_DATABASE_ADMIN_URL"),
        help="PostgreSQL URL for an administrative database (or TEST_DATABASE_ADMIN_URL).",
    )
    parser.add_argument(
        "--database",
        default=os.getenv("TEST_DATABASE_NAME", DEFAULT_TEST_DATABASE_NAME),
        help=f"Test database name (default: {DEFAULT_TEST_DATABASE_NAME}).",
    )
    arguments = parser.parse_args()
    if not arguments.admin_url:
        parser.error("--admin-url or TEST_DATABASE_ADMIN_URL is required")

    created = create_test_database(arguments.admin_url, arguments.database)
    action = "created" if created else "already exists"
    print(f"Test database {arguments.database!r} {action}.")


if __name__ == "__main__":
    main()
