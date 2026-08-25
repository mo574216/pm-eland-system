"""Verify AUTH-DB-001 against a migrated PostgreSQL database."""

from importlib.util import module_from_spec, spec_from_file_location
from os import environ
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import sqlalchemy as sa

from app.core.database import to_sync_database_url


def _revision() -> ModuleType:
    revision_path = Path(__file__).parents[1] / "alembic" / "versions" / "0002_identity_schema.py"
    spec = spec_from_file_location("identity_schema_revision", revision_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load identity migration: {revision_path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _governance_revision() -> ModuleType:
    revision_path = (
        Path(__file__).parents[1] / "alembic" / "versions" / "0014_governance_permissions.py"
    )
    spec = spec_from_file_location("governance_permission_revision", revision_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load governance migration: {revision_path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify_identity_schema(database_url: str) -> None:
    """Assert schema, canonical seeds, and repeatable seed execution."""
    revision = _revision()
    governance = _governance_revision()
    engine = sa.create_engine(to_sync_database_url(database_url))
    try:
        with engine.begin() as connection:
            revision.seed_identity_data(connection)
            revision.seed_identity_data(connection)

            inspector = sa.inspect(connection)
            _require(
                set(inspector.get_table_names()).issuperset(
                    {
                        "users",
                        "roles",
                        "permissions",
                        "user_roles",
                        "role_permissions",
                        "auth_sessions",
                        "audit_logs",
                    }
                ),
                "Identity tables do not match AUTH-DB-001.",
            )
            _require(
                {column["name"] for column in inspector.get_columns("users")}
                == {
                    "id",
                    "username",
                    "email",
                    "password_hash",
                    "first_name",
                    "last_name",
                    "display_name",
                    "is_active",
                    "failed_login_count",
                    "last_login_at",
                    "created_at",
                    "updated_at",
                    "version",
                },
                "The users table does not match the database specification.",
            )
            _require(
                any(
                    index["name"] == "idx_users_active" for index in inspector.get_indexes("users")
                ),
                "The users active-state index is missing.",
            )

            role_codes = set(connection.execute(sa.text("SELECT code FROM roles")).scalars())
            permission_codes = set(
                connection.execute(sa.text("SELECT code FROM permissions")).scalars()
            )
            expected_roles = {
                *(role["code"] for role in revision.ROLE_SEEDS),
                *(role[0] for role in governance.ROLE_SEEDS),
            }
            expected_permissions = {
                *(permission[1] for permission in revision.PERMISSION_SEEDS),
                *(permission[0] for permission in governance.PERMISSION_SEEDS),
                "IDENTITY_MANAGE",
            }
            _require(role_codes == expected_roles, "Canonical role seeds do not match.")
            _require(
                permission_codes == expected_permissions,
                "Canonical permission seeds do not match.",
            )

            grants = connection.execute(
                sa.text(
                    "SELECT roles.code, permissions.code FROM role_permissions "
                    "JOIN roles ON roles.id = role_permissions.role_id "
                    "JOIN permissions ON permissions.id = role_permissions.permission_id"
                )
            )
            actual_grants: dict[str, set[str]] = {code: set() for code in expected_roles}
            for role_code, permission_code in cast(Any, grants):
                actual_grants[role_code].add(permission_code)
            expected_grants = {
                role_code: set(grants) for role_code, grants in revision.ROLE_GRANTS.items()
            }
            expected_grants["SYSTEM_ADMIN"].add("IDENTITY_MANAGE")
            for role_code, grants in governance.ROLE_GRANTS.items():
                expected_grants.setdefault(role_code, set()).update(grants)
            _require(actual_grants == expected_grants, "Canonical role grants do not match.")
    finally:
        engine.dispose()


def main() -> None:
    database_url = environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to verify the identity schema.")
    verify_identity_schema(database_url)


if __name__ == "__main__":
    main()
