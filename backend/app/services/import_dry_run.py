"""Read-only import classification against generic metadata-defined entities."""

from collections.abc import Iterable
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePath
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DependencyUnavailableError,
    InvalidMetadataError,
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.models.entity import EntityObject
from app.models.identity import AuditLog
from app.models.import_job import ImportConflict, ImportJob, ImportMapping, ImportProfile
from app.models.metadata import AttributeDefinition, EntityType
from app.repositories.entity import EntityRepository
from app.repositories.import_job import ImportJobRepository
from app.repositories.metadata import MetadataRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.import_profile import (
    MATCHING_STRATEGY_ADAPTER,
    AttributeMatchKey,
    EntityIdMatchingStrategy,
    ImportMatchingStrategy,
    ParentKeyMatchingStrategy,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService
from app.services.entity import EntityReferenceResolver
from app.services.import_parser import ImportParseError, ImportParser, ImportSourceRow
from app.services.metadata_validation import MetadataValueValidator, ValidationMode
from app.services.storage import StorageError, StorageProvider


@dataclass(frozen=True, slots=True)
class ImportValidationIssue:
    row_number: int | None
    field: str
    code: str


@dataclass(frozen=True, slots=True)
class ImportDryRunSummary:
    rows_read: int
    rows_valid: int
    rows_invalid: int
    records_to_create: int
    records_to_update: int
    records_unchanged: int
    conflicts: int


@dataclass(frozen=True, slots=True)
class ImportDryRunResult:
    import_job_id: UUID
    status: str
    summary: ImportDryRunSummary
    validation_errors: tuple[ImportValidationIssue, ...]


class ImportDryRunService:
    """Analyze a private staged source without mutating canonical entities."""

    def __init__(
        self,
        session: AsyncSession,
        actor: AuthenticatedIdentity,
        storage: StorageProvider | None,
        parser: ImportParser | None = None,
    ) -> None:
        self.session = session
        self.actor = actor
        self.storage = storage
        self.parser = parser or ImportParser()
        self.authorization = AuthorizationService(actor)
        self.repository = ImportJobRepository(session)
        self.workspace_repository = WorkspaceRepository(session)
        self.metadata_repository = MetadataRepository(session)
        self.entity_repository = EntityRepository(session)
        self.validator = MetadataValueValidator(EntityReferenceResolver(self.entity_repository))

    async def _require_execute(self, workspace_id: UUID) -> None:
        workspace = await self.workspace_repository.accessible_workspace(
            workspace_id, self.actor.user.id
        )
        if workspace is None:
            raise WorkspaceAccessDeniedError
        effective = self.authorization.permission_codes | frozenset(
            await self.workspace_repository.workspace_permission_codes(
                workspace_id, self.actor.user.id
            )
        )
        if PermissionCode.IMPORT_EXECUTE.value not in effective:
            raise PermissionDeniedError

    async def assign_profile(
        self, job_id: UUID, profile_id: UUID, *, audit: AuditContext
    ) -> ImportJob:
        async with self.session.begin():
            job = await self.repository.accessible_job(job_id, self.actor.user.id, lock=True)
            if job is None:
                raise ResourceNotFoundError
            await self._require_execute(job.workspace_id)
            if job.status not in {"UPLOADED", "VALIDATION_FAILED", "READY_FOR_REVIEW"}:
                raise ResourceConflictError
            profile = await self.repository.accessible_profile(
                profile_id, job.workspace_id, self.actor.user.id
            )
            if profile is None or not job.source_object_key.endswith(profile.source_type.lower()):
                raise ResourceNotFoundError
            before_profile_id = job.import_profile_id
            job.import_profile_id = profile.id
            job.status = "UPLOADED"
            job.dry_run_summary = None
            await self.repository.clear_conflicts(job.id)
            self.repository.add_audit_log(
                self._audit(
                    job,
                    "IMPORT_PROFILE_ASSIGNED",
                    {"import_profile_id": str(before_profile_id) if before_profile_id else None},
                    {"import_profile_id": str(profile.id), "status": job.status},
                    audit,
                )
            )
            await self.repository.flush()
        return job

    async def dry_run(self, job_id: UUID, *, audit: AuditContext) -> ImportDryRunResult:
        if self.storage is None:
            raise DependencyUnavailableError
        async with self.session.begin():
            job = await self.repository.accessible_job(job_id, self.actor.user.id)
            if job is None:
                raise ResourceNotFoundError
            await self._require_execute(job.workspace_id)
            if job.status not in {"UPLOADED", "VALIDATION_FAILED", "READY_FOR_REVIEW"}:
                raise ResourceConflictError
            if job.import_profile_id is None:
                raise InvalidMetadataError({"field": "import_profile_id", "reason": "required"})
            profile = await self.repository.accessible_profile(
                job.import_profile_id, job.workspace_id, self.actor.user.id
            )
            if profile is None:
                raise ResourceNotFoundError
            mappings = await self.repository.profile_mappings(profile.id)
            entity_type = await self.metadata_repository.entity_type_in_workspace(
                profile.entity_type_id, job.workspace_id
            )
            if entity_type is None or not entity_type.is_active:
                raise InvalidMetadataError({"field": "entity_type_id", "reason": "inactive"})
            definitions = await self.metadata_repository.list_attributes(entity_type.id)
            entities = await self.repository.entities_for_type(job.workspace_id, entity_type.id)
            source_status = job.status
        try:
            payload = await self.storage.read_object(job.source_object_key)
        except StorageError as error:
            raise DependencyUnavailableError from error
        strategy = MATCHING_STRATEGY_ADAPTER.validate_python(profile.matching_strategy)
        selected_sheet = profile.configuration.get("selected_sheet")
        sheet_name = selected_sheet if isinstance(selected_sheet, str) else None
        filename = self._parser_filename(job.source_object_key, sheet_name)
        rows = self.parser.iter_rows(
            BytesIO(payload),
            filename=filename,
            sheet_name=sheet_name if profile.source_type == "XLSX" else None,
        )
        try:
            async with self.session.begin():
                result, conflicts = await self._classify(
                    job, profile, mappings, entity_type, definitions, entities, strategy, rows
                )
        except ImportParseError as error:
            raise InvalidMetadataError({"field": "file", "reason": error.reason.lower()}) from error
        async with self.session.begin():
            locked = await self.repository.accessible_job(job.id, self.actor.user.id, lock=True)
            if locked is None:
                raise ResourceNotFoundError
            if locked.import_profile_id != profile.id or locked.status != source_status:
                raise ResourceConflictError
            await self._require_execute(locked.workspace_id)
            await self.repository.clear_conflicts(locked.id)
            for conflict in conflicts:
                self.repository.add_conflict(conflict)
            locked.status = result.status
            locked.dry_run_summary = self._stored_result(result)
            self.repository.add_audit_log(
                self._audit(
                    locked,
                    "IMPORT_DRY_RUN_COMPLETED",
                    None,
                    {"status": result.status, "summary": self._summary_dict(result.summary)},
                    audit,
                )
            )
            await self.repository.flush()
        return result

    async def _classify(
        self,
        job: ImportJob,
        profile: ImportProfile,
        mappings: tuple[ImportMapping, ...],
        entity_type: EntityType,
        definitions: tuple[AttributeDefinition, ...],
        entities: tuple[EntityObject, ...],
        strategy: ImportMatchingStrategy,
        rows: Iterable[ImportSourceRow],
    ) -> tuple[ImportDryRunResult, tuple[ImportConflict, ...]]:
        definitions_by_id = {item.id: item for item in definitions}
        index = self._entity_index(entities, strategy, definitions_by_id)
        seen_keys: set[tuple[object, ...]] = set()
        issues: list[ImportValidationIssue] = []
        conflicts: list[ImportConflict] = []
        creates = updates = unchanged = valid = invalid = rows_read = 0
        for row in rows:
            rows_read += 1
            values, row_issues = self._mapped_values(row, mappings, definitions_by_id)
            fingerprint, match_issues = self._source_fingerprint(row, strategy, definitions_by_id)
            row_issues.extend(match_issues)
            if fingerprint is not None and fingerprint in seen_keys:
                row_issues.append(
                    ImportValidationIssue(row.row_number, "matching_key", "DUPLICATE_ROW")
                )
            elif fingerprint is not None:
                seen_keys.add(fingerprint)
            candidates = index.get(fingerprint, ()) if fingerprint is not None else ()
            if len(candidates) > 1:
                row_issues.append(
                    ImportValidationIssue(row.row_number, "matching_key", "AMBIGUOUS_MATCH")
                )
            existing = candidates[0] if len(candidates) == 1 else None
            mode = ValidationMode.UPDATE if existing else ValidationMode.CREATE
            validation = await self.validator.validate_attributes(
                entity_type, definitions, cast(dict[str, object], values["attributes"]), mode
            )
            row_issues.extend(
                ImportValidationIssue(row.row_number, item.field, item.code)
                for item in validation.errors
            )
            name = values.get("name")
            if existing is None and (not isinstance(name, str) or not name.strip()):
                row_issues.append(ImportValidationIssue(row.row_number, "name", "REQUIRED"))
            elif name is not None and (not isinstance(name, str) or len(name) > 255):
                row_issues.append(ImportValidationIssue(row.row_number, "name", "INVALID_TYPE"))
            description = values.get("description")
            if description is not None and not isinstance(description, str):
                row_issues.append(
                    ImportValidationIssue(row.row_number, "description", "INVALID_TYPE")
                )
            parent_id = values.get("parent_id")
            if parent_id is not None and not isinstance(parent_id, UUID):
                row_issues.append(
                    ImportValidationIssue(row.row_number, "parent_id", "INVALID_TYPE")
                )
            elif isinstance(parent_id, UUID) and not any(item.id == parent_id for item in entities):
                row_issues.append(
                    ImportValidationIssue(row.row_number, "parent_id", "REFERENCE_NOT_FOUND")
                )
            elif existing is not None and parent_id == existing.id:
                row_issues.append(
                    ImportValidationIssue(row.row_number, "parent_id", "HIERARCHY_CYCLE")
                )
            if row_issues:
                invalid += 1
                issues.extend(row_issues)
                continue
            valid += 1
            if existing is None:
                creates += 1
                continue
            changes = self._changes(existing, values, validation.values)
            if not changes:
                unchanged += 1
                continue
            updates += 1
            for field, old_value, new_value in changes:
                conflicts.append(
                    ImportConflict(
                        id=uuid4(),
                        import_job_id=job.id,
                        row_number=row.row_number,
                        entity_id=existing.id,
                        attribute_key=field,
                        existing_value=self._json_value(old_value),
                        imported_value=self._json_value(new_value),
                    )
                )
        summary = ImportDryRunSummary(
            rows_read=rows_read,
            rows_valid=valid,
            rows_invalid=invalid,
            records_to_create=creates,
            records_to_update=updates,
            records_unchanged=unchanged,
            conflicts=len(conflicts),
        )
        status = (
            "VALIDATION_FAILED"
            if invalid
            else "READY_FOR_REVIEW"
            if conflicts
            else "READY_TO_COMMIT"
        )
        return ImportDryRunResult(job.id, status, summary, tuple(issues)), tuple(conflicts)

    @staticmethod
    def _mapped_values(
        row: ImportSourceRow,
        mappings: tuple[ImportMapping, ...],
        definitions_by_id: dict[UUID, AttributeDefinition],
    ) -> tuple[dict[str, object], list[ImportValidationIssue]]:
        attributes: dict[str, object] = {}
        values: dict[str, object] = {"attributes": attributes}
        issues: list[ImportValidationIssue] = []
        for mapping in mappings:
            if mapping.source_sheet not in {None, row.sheet} and not row.sheet.endswith(".csv"):
                continue
            if mapping.source_column not in row.values:
                issues.append(
                    ImportValidationIssue(
                        row.row_number, mapping.source_column, "MISSING_SOURCE_COLUMN"
                    )
                )
                continue
            raw = row.values[mapping.source_column]
            value = (
                raw.strip()
                if isinstance(raw, str) and mapping.transformation_config.get("trim")
                else raw
            )
            if mapping.target_attribute_definition_id is not None:
                definition = definitions_by_id.get(mapping.target_attribute_definition_id)
                if definition is None:
                    issues.append(
                        ImportValidationIssue(
                            row.row_number, mapping.source_column, "INVALID_MAPPING"
                        )
                    )
                    continue
                attributes[definition.key] = ImportDryRunService._coerce(
                    value, definition.data_type
                )
            elif mapping.target_system_field == "parent_id":
                try:
                    values["parent_id"] = None if value in {None, ""} else UUID(str(value))
                except (ValueError, TypeError, AttributeError):
                    values["parent_id"] = value
            elif mapping.target_system_field is not None:
                values[mapping.target_system_field] = value
        return values, issues

    @staticmethod
    def _coerce(value: object, data_type: str) -> object:
        if value in {None, ""}:
            return None
        if not isinstance(value, str):
            return value
        try:
            if data_type == "INTEGER":
                return int(value)
            if data_type == "DECIMAL":
                return float(value)
            if data_type == "BOOLEAN" and value.casefold() in {"true", "false"}:
                return value.casefold() == "true"
        except ValueError:
            return value
        return value

    @staticmethod
    def _source_fingerprint(
        row: ImportSourceRow,
        strategy: ImportMatchingStrategy,
        definitions_by_id: dict[UUID, AttributeDefinition],
    ) -> tuple[tuple[object, ...] | None, list[ImportValidationIssue]]:
        if isinstance(strategy, EntityIdMatchingStrategy):
            raw = row.values.get(strategy.source_column)
            try:
                return ("ENTITY_ID", UUID(str(raw))), []
            except (ValueError, TypeError, AttributeError):
                return None, [
                    ImportValidationIssue(row.row_number, strategy.source_column, "INVALID_UUID")
                ]
        keys = ImportDryRunService._strategy_keys(strategy)
        parts: list[object] = []
        if isinstance(strategy, ParentKeyMatchingStrategy):
            raw_parent = row.values.get(strategy.parent_source_column)
            try:
                parts.append(UUID(str(raw_parent)))
            except (ValueError, TypeError, AttributeError):
                return None, [
                    ImportValidationIssue(
                        row.row_number, strategy.parent_source_column, "INVALID_UUID"
                    )
                ]
        for key in keys:
            value = row.values.get(key.source_column)
            if value in {None, ""}:
                return None, [ImportValidationIssue(row.row_number, key.source_column, "REQUIRED")]
            definition = (
                definitions_by_id.get(key.attribute_definition_id)
                if key.attribute_definition_id
                else None
            )
            parts.append(
                ImportDryRunService._coerce(value, definition.data_type) if definition else value
            )
        return (strategy.type, *parts), []

    @staticmethod
    def _strategy_keys(strategy: ImportMatchingStrategy) -> tuple[AttributeMatchKey, ...]:
        if hasattr(strategy, "keys"):
            return strategy.keys
        if hasattr(strategy, "key"):
            return (strategy.key,)
        return ()

    @staticmethod
    def _entity_index(
        entities: tuple[EntityObject, ...],
        strategy: ImportMatchingStrategy,
        definitions_by_id: dict[UUID, AttributeDefinition],
    ) -> dict[tuple[object, ...], tuple[EntityObject, ...]]:
        grouped: dict[tuple[object, ...], list[EntityObject]] = {}
        for entity in entities:
            if isinstance(strategy, EntityIdMatchingStrategy):
                grouped.setdefault(("ENTITY_ID", entity.id), []).append(entity)
                continue
            parts: list[object] = []
            if isinstance(strategy, ParentKeyMatchingStrategy):
                parts.append(entity.parent_id)
            for key in ImportDryRunService._strategy_keys(strategy):
                if key.system_field == "name":
                    parts.append(entity.name)
                elif key.attribute_definition_id is not None:
                    definition = definitions_by_id.get(key.attribute_definition_id)
                    parts.append(entity.attributes.get(definition.key) if definition else None)
            grouped.setdefault((strategy.type, *parts), []).append(entity)
        return {key: tuple(values) for key, values in grouped.items()}

    @staticmethod
    def _changes(
        entity: EntityObject, values: dict[str, object], attributes: dict[str, object]
    ) -> list[tuple[str, object | None, object | None]]:
        changes: list[tuple[str, object | None, object | None]] = []
        for field in ("name", "description", "parent_id"):
            if field in values and values[field] != getattr(entity, field):
                changes.append((field, getattr(entity, field), values[field]))
        for key, value in attributes.items():
            if entity.attributes.get(key) != value:
                changes.append((key, entity.attributes.get(key), value))
        return changes

    @staticmethod
    def _json_value(value: object | None) -> object | None:
        if isinstance(value, UUID):
            return str(value)
        return value

    @staticmethod
    def _parser_filename(object_key: str, selected_sheet: str | None) -> str:
        suffix = PurePath(object_key).suffix
        return f"{selected_sheet or 'source'}{suffix}"

    @staticmethod
    def _summary_dict(summary: ImportDryRunSummary) -> dict[str, int]:
        return {
            "rows_read": summary.rows_read,
            "rows_valid": summary.rows_valid,
            "rows_invalid": summary.rows_invalid,
            "records_to_create": summary.records_to_create,
            "records_to_update": summary.records_to_update,
            "records_unchanged": summary.records_unchanged,
            "conflicts": summary.conflicts,
        }

    @staticmethod
    def _stored_result(result: ImportDryRunResult) -> dict[str, object]:
        return {
            **ImportDryRunService._summary_dict(result.summary),
            "validation_errors": [
                {"row_number": item.row_number, "field": item.field, "code": item.code}
                for item in result.validation_errors
            ],
        }

    def _audit(
        self,
        job: ImportJob,
        action: str,
        before: dict[str, object] | None,
        after: dict[str, object],
        audit: AuditContext,
    ) -> AuditLog:
        return AuditLog(
            id=uuid4(),
            request_id=audit.request_id,
            workspace_id=job.workspace_id,
            user_id=self.actor.user.id,
            action=action,
            resource_type="import_job",
            resource_id=job.id,
            before_state=before,
            after_state=after,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )
