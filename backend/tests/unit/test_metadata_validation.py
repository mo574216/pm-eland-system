"""Generic metadata-driven value validation tests."""

from uuid import UUID, uuid4

import pytest

from app.models.metadata import AttributeDefinition, EntityType
from app.services.metadata_validation import MetadataValueValidator, ValidationMode


def entity_type() -> EntityType:
    return EntityType(
        id=uuid4(),
        workspace_id=uuid4(),
        key="generic_type",
        name="Generic Type",
        configuration={},
        is_active=True,
    )


def definition(key: str, data_type: str, **values: object) -> AttributeDefinition:
    attributes: dict[str, object] = {
        "validation_config": {},
        "display_config": {},
        "inheritance_config": {},
        "is_active": True,
    }
    attributes.update(values)
    return AttributeDefinition(
        id=uuid4(),
        entity_type_id=uuid4(),
        key=key,
        label=key,
        data_type=data_type,
        **attributes,
    )


@pytest.mark.asyncio
async def test_required_defaults_and_unknown_keys_are_generic() -> None:
    definitions = [
        definition("required_text", "TEXT", is_required=True),
        definition("with_default", "INTEGER", default_value=7),
    ]

    result = await MetadataValueValidator().validate_attributes(
        entity_type(), definitions, {"unknown": "value"}, ValidationMode.CREATE
    )

    assert result.values["with_default"] == 7
    assert {(error.field, error.code) for error in result.errors} == {
        ("required_text", "REQUIRED"),
        ("unknown", "UNKNOWN_ATTRIBUTE"),
    }


@pytest.mark.asyncio
async def test_data_types_do_not_accept_boolean_as_number() -> None:
    result = await MetadataValueValidator().validate_attributes(
        entity_type(),
        [definition("count", "INTEGER")],
        {"count": True},
        ValidationMode.CREATE,
    )

    assert result.errors[0].code == "INVALID_TYPE"


@pytest.mark.asyncio
async def test_enum_membership_and_numeric_string_constraints() -> None:
    definitions = [
        definition(
            "risk",
            "ENUM",
            display_config={"options": [{"value": "LOW", "label": "Low"}]},
        ),
        definition("score", "DECIMAL", validation_config={"minimum": 1, "maximum": 5}),
        definition(
            "code",
            "TEXT",
            validation_config={"min_length": 3, "max_length": 5, "pattern": "^[A-Z]+$"},
        ),
    ]

    result = await MetadataValueValidator().validate_attributes(
        entity_type(),
        definitions,
        {"risk": "HIGH", "score": 9, "code": "ab"},
        ValidationMode.UPDATE,
    )

    assert {error.code for error in result.errors} == {
        "INVALID_ENUM_VALUE",
        "MAXIMUM",
        "MIN_LENGTH",
        "PATTERN",
    }


@pytest.mark.asyncio
async def test_read_only_is_only_writable_in_system_mode() -> None:
    definitions = [definition("inherited", "TEXT", is_read_only=True)]
    validator = MetadataValueValidator()

    user_result = await validator.validate_attributes(
        entity_type(), definitions, {"inherited": "x"}, ValidationMode.UPDATE
    )
    system_result = await validator.validate_attributes(
        entity_type(), definitions, {"inherited": "x"}, ValidationMode.SYSTEM
    )

    assert user_result.errors[0].code == "READ_ONLY"
    assert system_result.is_valid


class FakeReferenceResolver:
    def __init__(self, existing: UUID) -> None:
        self.existing = existing

    async def exists(self, _: str, reference_id: UUID, __: UUID) -> bool:
        return reference_id == self.existing


@pytest.mark.asyncio
async def test_reference_existence_is_workspace_resolved() -> None:
    existing = uuid4()
    validator = MetadataValueValidator(FakeReferenceResolver(existing))
    definitions = [definition("owner", "USER_REFERENCE")]

    valid = await validator.validate_attributes(
        entity_type(), definitions, {"owner": str(existing)}, ValidationMode.CREATE
    )
    missing = await validator.validate_attributes(
        entity_type(), definitions, {"owner": str(uuid4())}, ValidationMode.CREATE
    )

    assert valid.is_valid
    assert missing.errors[0].code == "REFERENCE_NOT_FOUND"


def test_pattern_engine_rejects_high_risk_regex_constructs() -> None:
    assert MetadataValueValidator.is_safe_pattern("^[A-Z0-9_]+$")
    assert not MetadataValueValidator.is_safe_pattern("(a+)+$")
    assert not MetadataValueValidator.is_safe_pattern("a|b")
