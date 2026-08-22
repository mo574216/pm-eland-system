"""Verify META-DB-001 against a migrated PostgreSQL database."""

from os import environ

import sqlalchemy as sa

from app.core.database import to_sync_database_url
from app.models.metadata import SUPPORTED_ATTRIBUTE_TYPES


def verify_metadata_schema(database_url: str) -> None:
    engine = sa.create_engine(to_sync_database_url(database_url))
    try:
        with engine.connect() as connection:
            inspector = sa.inspect(connection)
            tables = set(inspector.get_table_names())
            if not {"entity_types", "attribute_definitions"}.issubset(tables):
                raise RuntimeError("Metadata tables do not match META-DB-001.")
            entity_indexes = {item["name"] for item in inspector.get_indexes("entity_types")}
            attribute_indexes = {
                item["name"] for item in inspector.get_indexes("attribute_definitions")
            }
            if not {"idx_entity_types_workspace", "idx_entity_types_active"}.issubset(
                entity_indexes
            ):
                raise RuntimeError("Entity-type workspace indexes are missing.")
            if not {
                "idx_attribute_definitions_type",
                "idx_attribute_definitions_active",
            }.issubset(attribute_indexes):
                raise RuntimeError("Attribute-definition indexes are missing.")
            checks = inspector.get_check_constraints("attribute_definitions")
            data_type_check = next(
                item for item in checks if item["name"] == "ck_attribute_definitions_data_type"
            )
            if not all(value in data_type_check["sqltext"] for value in SUPPORTED_ATTRIBUTE_TYPES):
                raise RuntimeError("Supported metadata data types do not match the contract.")
    finally:
        engine.dispose()


def main() -> None:
    database_url = environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to verify the metadata schema.")
    verify_metadata_schema(database_url)


if __name__ == "__main__":
    main()
