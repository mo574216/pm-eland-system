"""Verify ENT-DB-001 against a migrated PostgreSQL database."""

from os import environ

import sqlalchemy as sa

from app.core.database import to_sync_database_url


def verify_entity_schema(database_url: str) -> None:
    engine = sa.create_engine(to_sync_database_url(database_url))
    try:
        with engine.connect() as connection:
            inspector = sa.inspect(connection)
            if "entity_objects" not in inspector.get_table_names():
                raise RuntimeError("Generic entity table does not match ENT-DB-001.")
            columns = {column["name"]: column for column in inspector.get_columns("entity_objects")}
            if columns["attributes"]["type"].__class__.__name__ != "JSONB":
                raise RuntimeError("Entity attributes are not stored in canonical JSONB.")
            indexes = {item["name"] for item in inspector.get_indexes("entity_objects")}
            expected = {
                "idx_entity_objects_workspace",
                "idx_entity_objects_type",
                "idx_entity_objects_parent",
                "idx_entity_objects_name",
                "idx_entity_objects_attributes_gin",
            }
            if not expected.issubset(indexes):
                raise RuntimeError("Required generic entity indexes are missing.")
    finally:
        engine.dispose()


def main() -> None:
    database_url = environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to verify the entity schema.")
    verify_entity_schema(database_url)


if __name__ == "__main__":
    main()
