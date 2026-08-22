"""Verify WS-DB-001 against a migrated PostgreSQL database."""

from os import environ

import sqlalchemy as sa

from app.core.database import to_sync_database_url


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify_workspace_schema(database_url: str) -> None:
    """Assert workspace tables, constraints, indexes, and isolation foreign keys."""
    engine = sa.create_engine(to_sync_database_url(database_url))
    try:
        with engine.connect() as connection:
            inspector = sa.inspect(connection)
            _require(
                {"workspaces", "workspace_memberships"}.issubset(inspector.get_table_names()),
                "Workspace tables do not match WS-DB-001.",
            )
            _require(
                {column["name"] for column in inspector.get_columns("workspaces")}
                == {
                    "id",
                    "name",
                    "slug",
                    "description",
                    "owner_id",
                    "status",
                    "configuration",
                    "created_at",
                    "updated_at",
                    "archived_at",
                    "deleted_at",
                    "version",
                },
                "The workspaces table does not match the database specification.",
            )
            _require(
                {column["name"] for column in inspector.get_columns("workspace_memberships")}
                == {"id", "workspace_id", "user_id", "role_id", "status", "created_at"},
                "The workspace_memberships table does not match the database specification.",
            )

            workspace_indexes = {index["name"] for index in inspector.get_indexes("workspaces")}
            membership_indexes = {
                index["name"] for index in inspector.get_indexes("workspace_memberships")
            }
            _require(
                {"idx_workspaces_status", "idx_workspaces_owner"}.issubset(workspace_indexes),
                "Workspace lookup indexes are missing.",
            )
            _require(
                {
                    "idx_workspace_memberships_user",
                    "idx_workspace_memberships_workspace",
                }.issubset(membership_indexes),
                "Workspace membership isolation indexes are missing.",
            )

            unique_constraints = {
                constraint["name"]
                for constraint in inspector.get_unique_constraints("workspace_memberships")
            }
            _require(
                "uq_workspace_memberships_workspace_user" in unique_constraints,
                "Users can have duplicate memberships in a workspace.",
            )

            foreign_keys = {
                foreign_key["name"]: foreign_key
                for foreign_key in inspector.get_foreign_keys("workspace_memberships")
            }
            _require(
                foreign_keys["fk_workspace_memberships_workspace_id_workspaces"]["options"].get(
                    "ondelete"
                )
                == "CASCADE",
                "Workspace deletion does not cascade memberships.",
            )
            _require(
                foreign_keys["fk_workspace_memberships_user_id_users"]["options"].get("ondelete")
                == "CASCADE",
                "User deletion does not cascade workspace memberships.",
            )
            _require(
                foreign_keys["fk_workspace_memberships_role_id_roles"]["options"].get("ondelete")
                == "SET NULL",
                "Role deletion does not preserve workspace membership.",
            )
    finally:
        engine.dispose()


def main() -> None:
    database_url = environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to verify the workspace schema.")
    verify_workspace_schema(database_url)


if __name__ == "__main__":
    main()
