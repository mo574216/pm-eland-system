"""Generic draft form value validation against normalized render metadata."""

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.schemas.form import FormRenderField


class FormReferenceResolver(Protocol):
    async def exists(self, kind: str, reference_id: UUID, workspace_id: UUID) -> bool: ...


@dataclass(frozen=True)
class FormValueError:
    field: str
    code: str


class FormValueValidator:
    def __init__(self, reference_resolver: FormReferenceResolver) -> None:
        self.reference_resolver = reference_resolver

    async def validate_draft(
        self,
        fields: tuple[FormRenderField, ...],
        values: dict[str, object],
        workspace_id: UUID,
    ) -> tuple[FormValueError, ...]:
        by_key = {field.key: field for field in fields}
        errors = [FormValueError(key, "UNKNOWN_FIELD") for key in values.keys() - by_key.keys()]
        for key in values.keys() & by_key.keys():
            field = by_key[key]
            value = values[key]
            if not field.visible:
                errors.append(FormValueError(key, "HIDDEN"))
                continue
            if field.read_only:
                errors.append(FormValueError(key, "READ_ONLY"))
                continue
            if value is None:
                continue
            errors.extend(self._value_errors(key, field.type, value, field.configuration))
            if field.type in {"USER_REFERENCE", "ENTITY_REFERENCE", "FILE_REFERENCE"}:
                reference_id = self._uuid(value)
                if reference_id is not None and not await self.reference_resolver.exists(
                    field.type, reference_id, workspace_id
                ):
                    errors.append(FormValueError(key, "REFERENCE_NOT_FOUND"))
        return tuple(errors)

    def _value_errors(
        self, path: str, field_type: str, value: object, configuration: dict[str, object]
    ) -> list[FormValueError]:
        if not self._has_valid_type(field_type, value):
            return [FormValueError(path, "INVALID_TYPE")]
        errors: list[FormValueError] = []
        if isinstance(value, str):
            minimum = configuration.get("min_length")
            maximum = configuration.get("max_length")
            if isinstance(minimum, int) and len(value) < minimum:
                errors.append(FormValueError(path, "MIN_LENGTH"))
            if isinstance(maximum, int) and len(value) > maximum:
                errors.append(FormValueError(path, "MAX_LENGTH"))
            pattern = configuration.get("pattern")
            if isinstance(pattern, str) and not self._safe_pattern_match(pattern, value):
                errors.append(FormValueError(path, "PATTERN"))
        if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
            minimum = configuration.get("minimum")
            maximum = configuration.get("maximum")
            if isinstance(minimum, (int, float)) and value < minimum:
                errors.append(FormValueError(path, "MINIMUM"))
            if isinstance(maximum, (int, float)) and value > maximum:
                errors.append(FormValueError(path, "MAXIMUM"))
        if field_type in {"ENUM", "MULTI_ENUM"}:
            allowed = self._options(configuration.get("options"))
            selected = [value] if isinstance(value, str) else value
            if allowed is not None and isinstance(selected, list):
                if any(item not in allowed for item in selected):
                    errors.append(FormValueError(path, "INVALID_ENUM_VALUE"))
        if field_type == "TABLE" and isinstance(value, list):
            errors.extend(self._table_errors(path, value, configuration))
        return errors

    def _table_errors(
        self, path: str, rows: list[object], configuration: dict[str, object]
    ) -> list[FormValueError]:
        columns = configuration.get("columns")
        if not isinstance(columns, list):
            return [FormValueError(path, "INVALID_TABLE_CONFIGURATION")]
        definitions = {
            column["key"]: column
            for column in columns
            if isinstance(column, dict)
            and isinstance(column.get("key"), str)
            and isinstance(column.get("type"), str)
        }
        if len(definitions) != len(columns):
            return [FormValueError(path, "INVALID_TABLE_CONFIGURATION")]
        errors: list[FormValueError] = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(FormValueError(f"{path}.{index}", "INVALID_TYPE"))
                continue
            for key in row.keys() - definitions.keys():
                errors.append(FormValueError(f"{path}.{index}.{key}", "UNKNOWN_FIELD"))
            for key, definition in definitions.items():
                column_path = f"{path}.{index}.{key}"
                if key not in row or row[key] is None:
                    if definition.get("required") is True:
                        errors.append(FormValueError(column_path, "REQUIRED"))
                    continue
                column_type = str(definition["type"])
                column_config = definition.get("configuration", {})
                errors.extend(
                    self._value_errors(
                        column_path,
                        column_type,
                        row[key],
                        column_config if isinstance(column_config, dict) else {},
                    )
                )
        return errors

    @staticmethod
    def _has_valid_type(field_type: str, value: object) -> bool:
        if field_type in {"TEXT", "RICH_TEXT", "ENUM"}:
            return isinstance(value, str)
        if field_type == "INTEGER":
            return isinstance(value, int) and not isinstance(value, bool)
        if field_type == "DECIMAL":
            return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)
        if field_type == "BOOLEAN":
            return isinstance(value, bool)
        if field_type == "DATE":
            if isinstance(value, date) and not isinstance(value, datetime):
                return True
            if not isinstance(value, str):
                return False
            try:
                date.fromisoformat(value)
            except ValueError:
                return False
            return True
        if field_type == "DATETIME":
            if isinstance(value, datetime):
                return value.tzinfo is not None
            if not isinstance(value, str):
                return False
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return False
            return parsed.tzinfo is not None
        if field_type == "MULTI_ENUM":
            return isinstance(value, list) and all(isinstance(item, str) for item in value)
        if field_type in {"USER_REFERENCE", "ENTITY_REFERENCE", "FILE_REFERENCE"}:
            return FormValueValidator._uuid(value) is not None
        if field_type == "TABLE":
            return isinstance(value, list)
        return False

    @staticmethod
    def _options(value: object) -> set[str] | None:
        if not isinstance(value, list):
            return None
        options: set[str] = set()
        for option in value:
            if isinstance(option, str):
                options.add(option)
            elif isinstance(option, dict) and isinstance(option.get("value"), str):
                options.add(option["value"])
        return options

    @staticmethod
    def _safe_pattern_match(pattern: str, value: str) -> bool:
        if len(pattern) > 256 or len(value) > 10_000:
            return False
        if any(token in pattern for token in ("(", ")", "|")) or re.search(r"\\[1-9]", pattern):
            return False
        try:
            return re.fullmatch(pattern, value) is not None
        except re.error:
            return False

    @staticmethod
    def _uuid(value: object) -> UUID | None:
        try:
            return UUID(str(value))
        except (ValueError, TypeError, AttributeError):
            return None
