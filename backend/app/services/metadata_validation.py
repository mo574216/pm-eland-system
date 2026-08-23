"""Reusable validation of generic entity values against metadata definitions."""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.models.metadata import AttributeDefinition, EntityType


class ValidationMode(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class AttributeValidationError:
    field: str
    code: str


@dataclass(frozen=True)
class ValidationResult:
    values: dict[str, object]
    errors: tuple[AttributeValidationError, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors


class ReferenceResolver(Protocol):
    async def exists(self, kind: str, reference_id: UUID, workspace_id: UUID) -> bool: ...


class MetadataValueValidator:
    """Validate without branching on domain-specific entity or attribute names."""

    def __init__(self, reference_resolver: ReferenceResolver | None = None) -> None:
        self.reference_resolver = reference_resolver

    async def validate_attributes(
        self,
        entity_type: EntityType,
        definitions: Sequence[AttributeDefinition],
        values: Mapping[str, object],
        mode: ValidationMode,
    ) -> ValidationResult:
        definitions_by_key = {
            definition.key: definition
            for definition in definitions
            if definition.is_active and definition.deleted_at is None
        }
        normalized = dict(values)
        errors: list[AttributeValidationError] = []

        for key in values.keys() - definitions_by_key.keys():
            errors.append(AttributeValidationError(key, "UNKNOWN_ATTRIBUTE"))

        for key, definition in definitions_by_key.items():
            supplied = key in values
            if (
                not supplied
                and mode == ValidationMode.CREATE
                and definition.default_value is not None
            ):
                normalized[key] = definition.default_value
                supplied = True
            if not supplied:
                if definition.is_required and mode == ValidationMode.CREATE:
                    errors.append(AttributeValidationError(key, "REQUIRED"))
                continue
            value = normalized[key]
            if value is None:
                if definition.is_required:
                    errors.append(AttributeValidationError(key, "REQUIRED"))
                continue
            if definition.is_read_only and mode != ValidationMode.SYSTEM:
                errors.append(AttributeValidationError(key, "READ_ONLY"))
                continue
            if not self._has_valid_type(definition.data_type, value):
                errors.append(AttributeValidationError(key, "INVALID_TYPE"))
                continue
            errors.extend(self._constraint_errors(definition, value))
            errors.extend(await self._reference_errors(entity_type, definition, value))

        return ValidationResult(normalized, tuple(errors))

    @staticmethod
    def _has_valid_type(data_type: str, value: object) -> bool:
        if data_type in {"TEXT", "RICH_TEXT", "ENUM"}:
            return isinstance(value, str)
        if data_type == "INTEGER":
            return isinstance(value, int) and not isinstance(value, bool)
        if data_type == "DECIMAL":
            return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)
        if data_type == "BOOLEAN":
            return isinstance(value, bool)
        if data_type == "DATE":
            if isinstance(value, date) and not isinstance(value, datetime):
                return True
            if not isinstance(value, str):
                return False
            try:
                date.fromisoformat(value)
            except ValueError:
                return False
            return True
        if data_type == "DATETIME":
            if isinstance(value, datetime):
                return value.tzinfo is not None
            if not isinstance(value, str):
                return False
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return False
            return parsed.tzinfo is not None
        if data_type == "MULTI_ENUM":
            return isinstance(value, list) and all(isinstance(item, str) for item in value)
        if data_type in {"USER_REFERENCE", "ENTITY_REFERENCE", "FILE_REFERENCE"}:
            try:
                UUID(str(value))
            except (ValueError, TypeError, AttributeError):
                return False
            return True
        if data_type == "TABLE":
            return isinstance(value, list) and all(isinstance(row, dict) for row in value)
        if data_type == "JSON":
            return MetadataValueValidator._is_json_value(value)
        return False

    @staticmethod
    def _is_json_value(value: object) -> bool:
        if value is None or isinstance(value, (str, int, float, bool)):
            return True
        if isinstance(value, list):
            return all(MetadataValueValidator._is_json_value(item) for item in value)
        if isinstance(value, dict):
            return all(
                isinstance(key, str) and MetadataValueValidator._is_json_value(child)
                for key, child in value.items()
            )
        return False

    @staticmethod
    def _constraint_errors(
        definition: AttributeDefinition, value: object
    ) -> list[AttributeValidationError]:
        errors: list[AttributeValidationError] = []
        config = definition.validation_config
        if isinstance(value, str):
            minimum = config.get("min_length")
            maximum = config.get("max_length")
            if isinstance(minimum, int) and len(value) < minimum:
                errors.append(AttributeValidationError(definition.key, "MIN_LENGTH"))
            if isinstance(maximum, int) and len(value) > maximum:
                errors.append(AttributeValidationError(definition.key, "MAX_LENGTH"))
            pattern = config.get("pattern")
            if isinstance(pattern, str) and not MetadataValueValidator._safe_pattern_match(
                pattern, value
            ):
                errors.append(AttributeValidationError(definition.key, "PATTERN"))
        if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
            minimum = config.get("minimum")
            maximum = config.get("maximum")
            if isinstance(minimum, (int, float)) and value < minimum:
                errors.append(AttributeValidationError(definition.key, "MINIMUM"))
            if isinstance(maximum, (int, float)) and value > maximum:
                errors.append(AttributeValidationError(definition.key, "MAXIMUM"))
        options = definition.display_config.get("options")
        if definition.data_type in {"ENUM", "MULTI_ENUM"} and isinstance(options, list):
            allowed = {
                option["value"]
                for option in options
                if isinstance(option, dict) and isinstance(option.get("value"), str)
            }
            selected = [value] if isinstance(value, str) else value
            if isinstance(selected, list) and any(item not in allowed for item in selected):
                errors.append(AttributeValidationError(definition.key, "INVALID_ENUM_VALUE"))
        return errors

    @staticmethod
    def _safe_pattern_match(pattern: str, value: str) -> bool:
        if not MetadataValueValidator.is_safe_pattern(pattern) or len(value) > 10_000:
            return False
        try:
            return re.fullmatch(pattern, value) is not None
        except re.error:
            return False

    @staticmethod
    def is_safe_pattern(pattern: str) -> bool:
        if len(pattern) > 256:
            return False
        if any(token in pattern for token in ("(", ")", "|")) or re.search(r"\\[1-9]", pattern):
            return False
        try:
            re.compile(pattern)
        except re.error:
            return False
        return True

    async def _reference_errors(
        self,
        entity_type: EntityType,
        definition: AttributeDefinition,
        value: object,
    ) -> list[AttributeValidationError]:
        if definition.data_type not in {
            "USER_REFERENCE",
            "ENTITY_REFERENCE",
            "FILE_REFERENCE",
        }:
            return []
        if self.reference_resolver is None:
            return [AttributeValidationError(definition.key, "REFERENCE_RESOLVER_REQUIRED")]
        reference_id = UUID(str(value))
        exists = await self.reference_resolver.exists(
            definition.data_type, reference_id, entity_type.workspace_id
        )
        if not exists:
            return [AttributeValidationError(definition.key, "REFERENCE_NOT_FOUND")]
        return []
