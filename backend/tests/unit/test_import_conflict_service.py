"""Explicit import-conflict resolution authorization and state tests."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog, User
from app.models.import_job import ImportConflict, ImportJob
from app.models.workspace import Workspace
from app.repositories.import_job import ImportJobRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.import_conflict import ImportConflictService


class TransactionContext:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class FakeSession:
    def begin(self) -> TransactionContext:
        return TransactionContext()


class FakeWorkspaceRepository:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def accessible_workspace(self, workspace_id: UUID, _: UUID) -> Workspace | None:
        return self.workspace if workspace_id == self.workspace.id else None

    async def workspace_permission_codes(self, _: UUID, __: UUID) -> tuple[str, ...]:
        return ()


class FakeRepository:
    def __init__(self, job: ImportJob, conflicts: tuple[ImportConflict, ...]) -> None:
        self.job = job
        self.conflicts = conflicts
        self.audit_logs: list[AuditLog] = []

    async def accessible_job(
        self, job_id: UUID, _: UUID, *, lock: bool = False
    ) -> ImportJob | None:
        return self.job if job_id == self.job.id else None

    async def accessible_conflict(
        self, job_id: UUID, conflict_id: UUID, _: UUID, *, lock: bool = False
    ) -> ImportConflict | None:
        return next(
            (
                item
                for item in self.conflicts
                if item.import_job_id == job_id and item.id == conflict_id
            ),
            None,
        )

    async def conflicts_by_ids(
        self, job_id: UUID, conflict_ids: frozenset[UUID]
    ) -> tuple[ImportConflict, ...]:
        return tuple(
            item
            for item in self.conflicts
            if item.import_job_id == job_id and item.id in conflict_ids
        )

    async def unresolved_conflict_count(self, job_id: UUID) -> int:
        return sum(
            item.import_job_id == job_id and item.resolution is None for item in self.conflicts
        )

    async def flush(self) -> None:
        return None

    def add_audit_log(self, value: AuditLog) -> None:
        self.audit_logs.append(value)


def identity(*permissions: PermissionCode) -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="resolver",
        email="resolver@example.test",
        password_hash="unused-conflict-test",  # noqa: S106
        display_name="Resolver",
    )
    return AuthenticatedIdentity(
        user=user,
        roles=("ANALYST",),
        permissions=tuple(item.value for item in permissions),
    )


def service(
    actor: AuthenticatedIdentity,
) -> tuple[ImportConflictService, FakeRepository, tuple[ImportConflict, ...]]:
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    job = ImportJob(
        id=uuid4(),
        workspace_id=workspace.id,
        source_object_key="workspaces/a/imports/source.csv",
        status="READY_FOR_REVIEW",
    )
    conflicts = tuple(
        ImportConflict(
            id=uuid4(),
            import_job_id=job.id,
            row_number=index + 2,
            attribute_key="name",
            existing_value=f"Old {index}",
            imported_value=f"New {index}",
        )
        for index in range(2)
    )
    repository = FakeRepository(job, conflicts)
    result = ImportConflictService(cast(AsyncSession, FakeSession()), actor)
    result.repository = cast(ImportJobRepository, repository)
    result.workspace_repository = cast(WorkspaceRepository, FakeWorkspaceRepository(workspace))
    return result, repository, conflicts


def audit() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


@pytest.mark.asyncio
async def test_single_and_bulk_decisions_are_explicit_audited_and_unlock_commit() -> None:
    actor = identity(PermissionCode.IMPORT_EXECUTE)
    conflict_service, repository, conflicts = service(actor)

    first = await conflict_service.resolve_one(
        repository.job.id, conflicts[0].id, "MERGE", audit=audit()
    )
    assert first.unresolved == 1
    assert first.status == "READY_FOR_REVIEW"
    assert conflicts[0].resolution == "MERGE"
    assert conflicts[0].resolved_by == actor.user.id
    assert isinstance(conflicts[0].resolved_at, datetime)

    final = await conflict_service.resolve_bulk(
        repository.job.id, (conflicts[1].id,), "SKIP", audit=audit()
    )
    assert final.unresolved == 0
    assert final.status == "READY_TO_COMMIT"
    assert conflicts[1].resolution == "SKIP"
    assert repository.audit_logs[0].action == "IMPORT_CONFLICT_RESOLVED"
    assert repository.audit_logs[1].action == "IMPORT_CONFLICTS_RESOLVED_BULK"
    assert conflicts[1].resolved_at is not None
    assert conflicts[1].resolved_at.tzinfo == UTC


@pytest.mark.asyncio
async def test_missing_permission_and_foreign_conflict_are_rejected() -> None:
    unauthorized_service, repository, conflicts = service(identity())
    with pytest.raises(PermissionDeniedError):
        await unauthorized_service.resolve_one(
            repository.job.id, conflicts[0].id, "REPLACE", audit=audit()
        )

    authorized_service, repository, _ = service(identity(PermissionCode.IMPORT_EXECUTE))
    with pytest.raises(ResourceNotFoundError):
        await authorized_service.resolve_one(repository.job.id, uuid4(), "REPLACE", audit=audit())
