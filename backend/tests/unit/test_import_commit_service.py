"""Transactional import application and idempotency tests."""

from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ImportAlreadyCommittedError,
    ImportConflictsUnresolvedError,
)
from app.models.entity import EntityObject
from app.models.identity import AuditLog, User
from app.models.import_job import ImportConflict, ImportJob, ImportMapping, ImportProfile
from app.models.metadata import AttributeDefinition, EntityType
from app.repositories.entity import EntityRepository
from app.repositories.import_job import ImportJobRepository
from app.repositories.metadata import MetadataRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.import_profile import UniqueAttributeMatchingStrategy
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService
from app.services.import_commit import ImportCommitService, ImportCommitSummary
from app.services.import_dry_run import (
    ImportDryRunResult,
    ImportDryRunSummary,
)
from app.services.import_parser import ImportParser, ImportSourceRow
from app.services.metadata_validation import MetadataValueValidator
from app.services.storage import StorageProvider


class FakeEntityRepository:
    def __init__(self, entities: tuple[EntityObject, ...]) -> None:
        self.entities = {item.id: item for item in entities}
        self.created: list[EntityObject] = []
        self.audits: list[AuditLog] = []
        self.hierarchy_locks = 0

    def add_entity(self, entity: EntityObject) -> None:
        self.created.append(entity)
        self.entities[entity.id] = entity

    def add_audit_log(self, audit: AuditLog) -> None:
        self.audits.append(audit)

    async def update_entity(
        self, entity_id: UUID, expected_version: int, values: dict[str, object]
    ) -> EntityObject | None:
        entity = self.entities[entity_id]
        if entity.version != expected_version:
            return None
        for key, value in values.items():
            setattr(entity, key, value)
        entity.version += 1
        return entity

    async def acquire_hierarchy_lock(self, _: UUID) -> None:
        self.hierarchy_locks += 1

    async def would_create_cycle(self, _: UUID, __: UUID, ___: UUID) -> bool:
        return False


def actor() -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="committer",
        email="committer@example.test",
        password_hash="unused-commit-test",  # noqa: S106
        display_name="Committer",
    )
    return AuthenticatedIdentity(user=user, roles=("IMPORTER",), permissions=("IMPORT_EXECUTE",))


def audit() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


@pytest.mark.asyncio
async def test_apply_rows_creates_updates_skips_and_audits_generic_entities() -> None:
    identity = actor()
    workspace_id = uuid4()
    entity_type = EntityType(
        id=uuid4(),
        workspace_id=workspace_id,
        key="item",
        name="Item",
        configuration={},
        is_active=True,
        version=1,
    )
    code = AttributeDefinition(
        id=uuid4(),
        entity_type_id=entity_type.id,
        key="code",
        label="Code",
        data_type="TEXT",
        is_required=True,
        validation_config={},
        display_config={},
        inheritance_config={},
        display_order=0,
        is_active=True,
        version=1,
    )
    profile_id = uuid4()
    mappings = (
        ImportMapping(
            id=uuid4(),
            import_profile_id=profile_id,
            source_column="Name",
            target_system_field="name",
            transformation_config={},
            display_order=0,
        ),
        ImportMapping(
            id=uuid4(),
            import_profile_id=profile_id,
            source_column="Code",
            target_attribute_definition_id=code.id,
            transformation_config={},
            display_order=1,
        ),
    )
    updated_entity = EntityObject(
        id=uuid4(),
        workspace_id=workspace_id,
        entity_type_id=entity_type.id,
        name="Old",
        status="ACTIVE",
        attributes={"code": "A"},
        version=1,
    )
    skipped_entity = EntityObject(
        id=uuid4(),
        workspace_id=workspace_id,
        entity_type_id=entity_type.id,
        name="Keep",
        status="ACTIVE",
        attributes={"code": "C"},
        version=1,
    )
    repository = FakeEntityRepository((updated_entity, skipped_entity))
    service = object.__new__(ImportCommitService)
    service.actor = identity
    service.validator = MetadataValueValidator()
    service.entity_repository = cast(EntityRepository, repository)
    job = ImportJob(
        id=uuid4(),
        workspace_id=workspace_id,
        import_profile_id=profile_id,
        source_object_key="workspaces/a/imports/source.csv",
        status="READY_TO_COMMIT",
    )
    strategy = UniqueAttributeMatchingStrategy.model_validate(
        {
            "type": "UNIQUE_ATTRIBUTE",
            "key": {"source_column": "Code", "attribute_definition_id": str(code.id)},
        }
    )
    rows = (
        ImportSourceRow("items.csv", 2, {"Name": "New", "Code": "A"}),
        ImportSourceRow("items.csv", 3, {"Name": "Created", "Code": "B"}),
        ImportSourceRow("items.csv", 4, {"Name": "Changed", "Code": "C"}),
    )
    conflicts = (
        ImportConflict(
            id=uuid4(),
            import_job_id=job.id,
            row_number=2,
            entity_id=updated_entity.id,
            attribute_key="name",
            existing_value="Old",
            imported_value="New",
            resolution="MERGE",
        ),
        ImportConflict(
            id=uuid4(),
            import_job_id=job.id,
            row_number=4,
            entity_id=skipped_entity.id,
            attribute_key="name",
            existing_value="Keep",
            imported_value="Changed",
            resolution="SKIP",
        ),
    )

    summary = await service._apply_rows(
        job,
        mappings,
        entity_type,
        (code,),
        (updated_entity, skipped_entity),
        strategy,
        rows,
        conflicts,
        audit(),
    )

    assert summary == ImportCommitSummary(3, 1, 1, 0, 1, 2, 0)
    assert updated_entity.name == "New"
    assert skipped_entity.name == "Keep"
    assert repository.created[0].attributes == {"code": "B"}
    assert [item.action for item in repository.audits] == [
        "ENTITY_UPDATED_BY_IMPORT",
        "ENTITY_CREATED_BY_IMPORT",
    ]


def test_commit_rejects_changed_or_unresolved_preview_and_replays_same_key() -> None:
    service = object.__new__(ImportCommitService)
    job = ImportJob(
        id=uuid4(),
        workspace_id=uuid4(),
        source_object_key="source.csv",
        status="READY_TO_COMMIT",
        dry_run_summary={
            "rows_read": 1,
            "rows_valid": 1,
            "rows_invalid": 0,
            "records_to_create": 0,
            "records_to_update": 1,
            "records_unchanged": 0,
            "conflicts": 1,
        },
    )
    preview = ImportDryRunResult(
        job.id,
        "READY_FOR_REVIEW",
        ImportDryRunSummary(1, 1, 0, 0, 1, 0, 1),
        (),
    )
    current = ImportConflict(
        id=uuid4(),
        import_job_id=job.id,
        row_number=2,
        attribute_key="name",
        existing_value="Old",
        imported_value="New",
    )
    with pytest.raises(ImportConflictsUnresolvedError):
        service._verify_dry_run(job, preview, (current,), (current,))

    summary = ImportCommitSummary(1, 0, 1, 0, 0, 1, 0)
    job.status = "COMPLETED"
    job.idempotency_key = "same-key"
    job.final_summary = ImportCommitService._commit_summary_dict(summary)
    assert service._completed_retry(job, "same-key").summary == summary
    with pytest.raises(ImportAlreadyCommittedError):
        service._completed_retry(job, "different-key")


class RollbackTransaction:
    def __init__(self, canonical: list[str], job: ImportJob) -> None:
        self.canonical = canonical
        self.job = job
        self.before: list[str] = []
        self.job_before: tuple[str, str | None] = (job.status, job.idempotency_key)

    async def __aenter__(self) -> None:
        self.before = list(self.canonical)

    async def __aexit__(self, error_type: object, *_: object) -> None:
        if error_type is not None:
            self.canonical[:] = self.before
            self.job.status, self.job.idempotency_key = self.job_before


class RollbackSession:
    def __init__(self, canonical: list[str], job: ImportJob) -> None:
        self.canonical = canonical
        self.job = job

    def begin(self) -> RollbackTransaction:
        return RollbackTransaction(self.canonical, self.job)


class CommitRepositoryProbe:
    def __init__(self, job: ImportJob, profile: ImportProfile) -> None:
        self.job = job
        self.profile = profile

    async def accessible_job(self, _: UUID, __: UUID, *, lock: bool = False) -> ImportJob:
        return self.job

    async def job_by_idempotency_key(self, _: UUID, __: str) -> None:
        return None

    async def accessible_profile(self, *_: object) -> ImportProfile:
        return self.profile

    async def profile_mappings(self, _: UUID) -> tuple[ImportMapping, ...]:
        return ()

    async def entities_for_type(self, *_: object) -> tuple[EntityObject, ...]:
        return ()

    async def all_conflicts(self, _: UUID) -> tuple[ImportConflict, ...]:
        return ()

    def add_audit_log(self, _: AuditLog) -> None:
        return None

    async def flush(self) -> None:
        return None


class WorkspaceProbe:
    async def accessible_workspace(self, workspace_id: UUID, _: UUID) -> object:
        return object()

    async def workspace_permission_codes(self, _: UUID, __: UUID) -> tuple[str, ...]:
        return ()


class MetadataProbe:
    def __init__(self, entity_type: EntityType) -> None:
        self.entity_type = entity_type

    async def entity_type_in_workspace(self, *_: object) -> EntityType:
        return self.entity_type

    async def list_attributes(self, _: UUID) -> tuple[AttributeDefinition, ...]:
        return ()


class StorageProbe:
    async def read_object(self, _: str) -> bytes:
        return b"Name\nCreated\n"


class RollbackProbeService(ImportCommitService):
    def __init__(self, canonical: list[str]) -> None:
        self.canonical = canonical

    async def _classify(
        self, *args: object
    ) -> tuple[ImportDryRunResult, tuple[ImportConflict, ...]]:
        return (
            ImportDryRunResult(
                cast(ImportJob, args[0]).id,
                "READY_TO_COMMIT",
                ImportDryRunSummary(1, 1, 0, 1, 0, 0, 0),
                (),
            ),
            (),
        )

    async def _apply_rows(self, *args: object, **kwargs: object) -> ImportCommitSummary:
        self.canonical.append("partial-write")
        raise RuntimeError("forced canonical failure")


@pytest.mark.asyncio
async def test_commit_transaction_rolls_back_a_forced_canonical_failure() -> None:
    identity = actor()
    workspace_id = uuid4()
    entity_type = EntityType(
        id=uuid4(),
        workspace_id=workspace_id,
        key="item",
        name="Item",
        configuration={},
        is_active=True,
        version=1,
    )
    profile = ImportProfile(
        id=uuid4(),
        workspace_id=workspace_id,
        entity_type_id=entity_type.id,
        name="Items",
        source_type="CSV",
        matching_strategy={"type": "ENTITY_ID", "source_column": "ID"},
        configuration={},
    )
    job = ImportJob(
        id=uuid4(),
        workspace_id=workspace_id,
        import_profile_id=profile.id,
        source_object_key="workspaces/a/imports/source.csv",
        status="READY_TO_COMMIT",
        dry_run_summary={
            "rows_read": 1,
            "rows_valid": 1,
            "rows_invalid": 0,
            "records_to_create": 1,
            "records_to_update": 0,
            "records_unchanged": 0,
            "conflicts": 0,
        },
    )
    canonical = ["existing"]
    service = RollbackProbeService(canonical)
    service.session = cast(AsyncSession, RollbackSession(canonical, job))
    service.actor = identity
    service.authorization = AuthorizationService(identity)
    service.storage = cast(StorageProvider, StorageProbe())
    service.repository = cast(ImportJobRepository, CommitRepositoryProbe(job, profile))
    service.workspace_repository = cast(WorkspaceRepository, WorkspaceProbe())
    service.metadata_repository = cast(MetadataRepository, MetadataProbe(entity_type))
    service.parser = cast(
        ImportParser,
        type("ParserProbe", (), {"iter_rows": lambda *_args, **_kwargs: iter(())})(),
    )

    with pytest.raises(RuntimeError, match="forced canonical failure"):
        await service.commit(job.id, idempotency_key="rollback-key", audit=audit())

    assert canonical == ["existing"]
    assert job.status == "READY_TO_COMMIT"
