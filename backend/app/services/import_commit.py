"""Transactional application of a reviewed generic import."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DependencyUnavailableError,
    ImportAlreadyCommittedError,
    ImportConflictsUnresolvedError,
    ImportValidationFailedError,
    ResourceConflictError,
    ResourceNotFoundError,
    StaleVersionError,
)
from app.models.entity import EntityObject
from app.models.identity import AuditLog
from app.models.import_job import ImportConflict, ImportJob, ImportMapping
from app.models.metadata import AttributeDefinition, EntityType
from app.schemas.import_profile import (
    MATCHING_STRATEGY_ADAPTER,
    ImportMatchingStrategy,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.import_dry_run import ImportDryRunResult, ImportDryRunService
from app.services.import_parser import ImportParseError, ImportSourceRow
from app.services.metadata_validation import ValidationMode
from app.services.storage import StorageError, StorageProvider


@dataclass(frozen=True, slots=True)
class ImportCommitSummary:
    rows_read: int
    records_created: int
    records_updated: int
    records_unchanged: int
    records_skipped: int
    conflicts_resolved: int
    invalid_rows: int


@dataclass(frozen=True, slots=True)
class ImportCommitResult:
    import_job_id: UUID
    status: str
    summary: ImportCommitSummary


class ImportCommitService(ImportDryRunService):
    def __init__(
        self,
        session: AsyncSession,
        actor: AuthenticatedIdentity,
        storage: StorageProvider | None,
    ) -> None:
        super().__init__(session, actor, storage)

    async def commit(
        self,
        job_id: UUID,
        *,
        idempotency_key: str | None,
        audit: AuditContext,
    ) -> ImportCommitResult:
        if self.storage is None:
            raise DependencyUnavailableError
        effective_key = idempotency_key or f"import-job:{job_id}"
        if len(effective_key) > 255:
            raise ResourceConflictError
        async with self.session.begin():
            snapshot = await self.repository.accessible_job(job_id, self.actor.user.id)
            if snapshot is None:
                raise ResourceNotFoundError
            await self._require_execute(snapshot.workspace_id)
            if snapshot.status == "COMPLETED":
                return self._completed_retry(snapshot, effective_key)
            if snapshot.status == "VALIDATION_FAILED":
                raise ImportValidationFailedError
            if snapshot.status != "READY_TO_COMMIT":
                raise ImportConflictsUnresolvedError
            source_object_key = snapshot.source_object_key
        try:
            payload = await self.storage.read_object(source_object_key)
        except StorageError as error:
            raise DependencyUnavailableError from error
        try:
            async with self.session.begin():
                job = await self.repository.accessible_job(job_id, self.actor.user.id, lock=True)
                if job is None:
                    raise ResourceNotFoundError
                await self._require_execute(job.workspace_id)
                if job.status == "COMPLETED":
                    return self._completed_retry(job, effective_key)
                if job.status == "VALIDATION_FAILED":
                    raise ImportValidationFailedError
                if job.status != "READY_TO_COMMIT" or job.import_profile_id is None:
                    raise ImportConflictsUnresolvedError
                duplicate = await self.repository.job_by_idempotency_key(
                    job.workspace_id, effective_key
                )
                if duplicate is not None and duplicate.id != job.id:
                    raise ResourceConflictError
                job.idempotency_key = effective_key
                job.status = "COMMITTING"
                job.started_at = datetime.now(UTC)
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
                    raise ResourceConflictError
                definitions = await self.metadata_repository.list_attributes(entity_type.id)
                entities = await self.repository.entities_for_type(job.workspace_id, entity_type.id)
                strategy = MATCHING_STRATEGY_ADAPTER.validate_python(profile.matching_strategy)
                selected_sheet = profile.configuration.get("selected_sheet")
                sheet_name = selected_sheet if isinstance(selected_sheet, str) else None
                filename = self._parser_filename(job.source_object_key, sheet_name)
                preview_rows = self.parser.iter_rows(
                    BytesIO(payload),
                    filename=filename,
                    sheet_name=sheet_name if profile.source_type == "XLSX" else None,
                )
                preview, recalculated_conflicts = await self._classify(
                    job,
                    profile,
                    mappings,
                    entity_type,
                    definitions,
                    entities,
                    strategy,
                    preview_rows,
                )
                persisted_conflicts = await self.repository.all_conflicts(job.id)
                self._verify_dry_run(job, preview, recalculated_conflicts, persisted_conflicts)
                rows = self.parser.iter_rows(
                    BytesIO(payload),
                    filename=filename,
                    sheet_name=sheet_name if profile.source_type == "XLSX" else None,
                )
                summary = await self._apply_rows(
                    job,
                    mappings,
                    entity_type,
                    definitions,
                    entities,
                    strategy,
                    rows,
                    persisted_conflicts,
                    audit,
                )
                job.status = "COMPLETED"
                job.final_summary = self._commit_summary_dict(summary)
                job.completed_at = datetime.now(UTC)
                self.repository.add_audit_log(
                    self._audit(
                        job,
                        "IMPORT_COMMITTED",
                        None,
                        {
                            "source_object_key": job.source_object_key,
                            "import_profile_id": str(profile.id),
                            "summary": self._commit_summary_dict(summary),
                            "status": job.status,
                        },
                        audit,
                    )
                )
                await self.repository.flush()
        except IntegrityError as error:
            raise ResourceConflictError from error
        except ImportParseError as error:
            raise ResourceConflictError from error
        return ImportCommitResult(job.id, job.status, summary)

    def _verify_dry_run(
        self,
        job: ImportJob,
        preview: ImportDryRunResult,
        recalculated_conflicts: tuple[ImportConflict, ...],
        persisted_conflicts: tuple[ImportConflict, ...],
    ) -> None:
        if preview.validation_errors or job.dry_run_summary is None:
            raise ImportValidationFailedError
        expected = self._summary_dict_from_preview(preview)
        if any(job.dry_run_summary.get(key) != value for key, value in expected.items()):
            raise ResourceConflictError
        persisted = {(item.row_number, item.attribute_key): item for item in persisted_conflicts}
        if len(persisted) != len(persisted_conflicts) or len(persisted) != len(
            recalculated_conflicts
        ):
            raise ResourceConflictError
        for current in recalculated_conflicts:
            saved = persisted.get((current.row_number, current.attribute_key))
            if (
                saved is None
                or saved.resolution is None
                or saved.existing_value != current.existing_value
                or saved.imported_value != current.imported_value
            ):
                raise ImportConflictsUnresolvedError

    async def _apply_rows(
        self,
        job: ImportJob,
        mappings: tuple[ImportMapping, ...],
        entity_type: EntityType,
        definitions: tuple[AttributeDefinition, ...],
        entities: tuple[EntityObject, ...],
        strategy: ImportMatchingStrategy,
        rows: Iterable[ImportSourceRow],
        conflicts: tuple[ImportConflict, ...],
        audit: AuditContext,
    ) -> ImportCommitSummary:
        definitions_by_id = {item.id: item for item in definitions}
        entity_index = self._entity_index(entities, strategy, definitions_by_id)
        decisions = {(item.row_number, item.attribute_key): item.resolution for item in conflicts}
        created = updated = unchanged = skipped = rows_read = 0
        hierarchy_locked = False
        for row in rows:
            rows_read += 1
            values, mapping_issues = self._mapped_values(row, mappings, definitions_by_id)
            fingerprint, match_issues = self._source_fingerprint(row, strategy, definitions_by_id)
            if mapping_issues or match_issues or fingerprint is None:
                raise ResourceConflictError
            candidates = entity_index.get(fingerprint, ())
            if len(candidates) > 1:
                raise ResourceConflictError
            existing = candidates[0] if candidates else None
            mode = ValidationMode.UPDATE if existing else ValidationMode.CREATE
            imported_attributes = cast(dict[str, object], values["attributes"])
            validation = await self.validator.validate_attributes(
                entity_type, definitions, imported_attributes, mode
            )
            if not validation.is_valid:
                raise ResourceConflictError
            if existing is None:
                name = values.get("name")
                if not isinstance(name, str) or not name.strip():
                    raise ResourceConflictError
                parent_id = values.get("parent_id")
                if parent_id is not None and not isinstance(parent_id, UUID):
                    raise ResourceConflictError
                entity = EntityObject(
                    id=uuid4(),
                    workspace_id=job.workspace_id,
                    entity_type_id=entity_type.id,
                    parent_id=parent_id,
                    name=name,
                    description=cast(str | None, values.get("description")),
                    status="ACTIVE",
                    attributes=validation.values,
                    created_by=self.actor.user.id,
                    updated_by=self.actor.user.id,
                    version=1,
                )
                self.entity_repository.add_entity(entity)
                self.entity_repository.add_audit_log(
                    self._entity_audit(entity, "ENTITY_CREATED_BY_IMPORT", None, audit)
                )
                created += 1
                continue
            changes = self._changes(existing, values, validation.values)
            if not changes:
                unchanged += 1
                continue
            system_updates: dict[str, object] = {}
            attribute_updates: dict[str, object] = {}
            for field, old_value, new_value in changes:
                resolution = decisions.get((row.row_number, field))
                if resolution is None:
                    raise ImportConflictsUnresolvedError
                if resolution == "SKIP":
                    continue
                chosen = (
                    self._merge_value(old_value, new_value) if resolution == "MERGE" else new_value
                )
                if field in {"name", "description", "parent_id"}:
                    system_updates[field] = chosen
                else:
                    attribute_updates[field] = chosen
            if not system_updates and not attribute_updates:
                skipped += 1
                continue
            if "parent_id" in system_updates:
                parent_id = system_updates["parent_id"]
                if parent_id is not None and not isinstance(parent_id, UUID):
                    raise ResourceConflictError
                if not hierarchy_locked:
                    await self.entity_repository.acquire_hierarchy_lock(job.workspace_id)
                    hierarchy_locked = True
                if parent_id == existing.id or (
                    isinstance(parent_id, UUID)
                    and await self.entity_repository.would_create_cycle(
                        existing.id, parent_id, job.workspace_id
                    )
                ):
                    raise ResourceConflictError
            before = self._entity_state(existing)
            update_values = dict(system_updates)
            if attribute_updates:
                update_values["attributes"] = {**existing.attributes, **attribute_updates}
            update_values["updated_by"] = self.actor.user.id
            changed = await self.entity_repository.update_entity(
                existing.id, existing.version, update_values
            )
            if changed is None:
                raise StaleVersionError
            self.entity_repository.add_audit_log(
                self._entity_audit(
                    changed,
                    "ENTITY_UPDATED_BY_IMPORT",
                    before,
                    audit,
                )
            )
            updated += 1
        return ImportCommitSummary(
            rows_read=rows_read,
            records_created=created,
            records_updated=updated,
            records_unchanged=unchanged,
            records_skipped=skipped,
            conflicts_resolved=len(conflicts),
            invalid_rows=0,
        )

    @staticmethod
    def _merge_value(existing: object | None, imported: object | None) -> object | None:
        if isinstance(existing, dict) and isinstance(imported, dict):
            return {**existing, **imported}
        if isinstance(existing, list) and isinstance(imported, list):
            merged = list(existing)
            for item in imported:
                if item not in merged:
                    merged.append(item)
            return merged
        return imported

    @staticmethod
    def _entity_state(entity: EntityObject) -> dict[str, object]:
        return {
            "entity_type_id": str(entity.entity_type_id),
            "parent_id": str(entity.parent_id) if entity.parent_id else None,
            "name": entity.name,
            "description": entity.description,
            "status": entity.status,
            "attributes": entity.attributes,
            "version": entity.version,
        }

    def _entity_audit(
        self,
        entity: EntityObject,
        action: str,
        before: dict[str, object] | None,
        audit: AuditContext,
    ) -> AuditLog:
        return AuditLog(
            id=uuid4(),
            request_id=audit.request_id,
            workspace_id=entity.workspace_id,
            user_id=self.actor.user.id,
            action=action,
            resource_type="entity_object",
            resource_id=entity.id,
            before_state=before,
            after_state=self._entity_state(entity),
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )

    @staticmethod
    def _completed_retry(job: ImportJob, effective_key: str) -> ImportCommitResult:
        if job.idempotency_key != effective_key or job.final_summary is None:
            raise ImportAlreadyCommittedError
        summary = ImportCommitSummary(
            rows_read=cast(int, job.final_summary["rows_read"]),
            records_created=cast(int, job.final_summary["records_created"]),
            records_updated=cast(int, job.final_summary["records_updated"]),
            records_unchanged=cast(int, job.final_summary["records_unchanged"]),
            records_skipped=cast(int, job.final_summary["records_skipped"]),
            conflicts_resolved=cast(int, job.final_summary["conflicts_resolved"]),
            invalid_rows=cast(int, job.final_summary["invalid_rows"]),
        )
        return ImportCommitResult(job.id, job.status, summary)

    @staticmethod
    def _summary_dict_from_preview(result: ImportDryRunResult) -> dict[str, int]:
        return {
            "rows_read": result.summary.rows_read,
            "rows_valid": result.summary.rows_valid,
            "rows_invalid": result.summary.rows_invalid,
            "records_to_create": result.summary.records_to_create,
            "records_to_update": result.summary.records_to_update,
            "records_unchanged": result.summary.records_unchanged,
            "conflicts": result.summary.conflicts,
        }

    @staticmethod
    def _commit_summary_dict(summary: ImportCommitSummary) -> dict[str, object]:
        return {
            "rows_read": summary.rows_read,
            "records_created": summary.records_created,
            "records_updated": summary.records_updated,
            "records_unchanged": summary.records_unchanged,
            "records_skipped": summary.records_skipped,
            "conflicts_resolved": summary.conflicts_resolved,
            "invalid_rows": summary.invalid_rows,
        }
