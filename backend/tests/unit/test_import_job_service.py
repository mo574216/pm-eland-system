"""Authorized import upload and inspection tests."""

from io import BytesIO
from typing import BinaryIO, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog, User
from app.models.import_job import ImportJob, ImportProfile
from app.models.workspace import Workspace
from app.repositories.import_job import ImportJobRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.import_job import ImportJobService, ImportUpload
from app.services.storage import StorageProvider


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
    def __init__(self, profile: ImportProfile | None = None) -> None:
        self.profile = profile
        self.jobs: list[ImportJob] = []
        self.audit_logs: list[AuditLog] = []

    def add_job(self, value: ImportJob) -> None:
        self.jobs.append(value)

    def add_audit_log(self, value: AuditLog) -> None:
        self.audit_logs.append(value)

    async def flush(self) -> None:
        return None

    async def accessible_profile(
        self, profile_id: UUID, workspace_id: UUID, _: UUID
    ) -> ImportProfile | None:
        if (
            self.profile is not None
            and self.profile.id == profile_id
            and self.profile.workspace_id == workspace_id
        ):
            return self.profile
        return None


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def put_object(
        self, object_key: str, data: BinaryIO, *, length: int, content_type: str
    ) -> None:
        value = data.read()
        assert len(value) == length
        assert content_type == "text/csv"
        self.objects[object_key] = value

    async def delete_object(self, object_key: str) -> None:
        self.objects.pop(object_key, None)

    async def object_exists(self, object_key: str) -> bool:
        return object_key in self.objects

    async def create_download_url(self, object_key: str) -> str:
        return object_key

    async def create_upload_url(self, object_key: str) -> str:
        return object_key


def identity(*permissions: PermissionCode) -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="importer",
        email="importer@example.test",
        password_hash="unused-import-job-test",  # noqa: S106
        display_name="Importer",
    )
    return AuthenticatedIdentity(
        user=user,
        roles=("ANALYST",),
        permissions=tuple(item.value for item in permissions),
    )


def service(
    actor: AuthenticatedIdentity, workspace: Workspace, profile: ImportProfile | None = None
) -> tuple[ImportJobService, FakeRepository, FakeStorage]:
    result = ImportJobService(
        cast(AsyncSession, FakeSession()), actor, cast(StorageProvider, FakeStorage())
    )
    repository = FakeRepository(profile)
    storage = cast(FakeStorage, result.storage)
    result.repository = cast(ImportJobRepository, repository)
    result.workspace_repository = cast(WorkspaceRepository, FakeWorkspaceRepository(workspace))
    return result, repository, storage


def audit() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


@pytest.mark.asyncio
async def test_upload_is_private_audited_and_returns_real_inspection() -> None:
    actor = identity(PermissionCode.IMPORT_EXECUTE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    import_service, repository, storage = service(actor, workspace)

    result = await import_service.upload_and_inspect(
        workspace.id,
        ImportUpload("people.csv", "text/csv", BytesIO(b"Name,Score\nAli,4\n"), None),
        audit=audit(),
    )

    assert result.status == "UPLOADED"
    assert result.inspection.sheets[0].columns[0].name == "Name"
    assert result.inspection.sheets[0].row_count == 1
    assert repository.jobs[0].source_object_key.startswith(f"workspaces/{workspace.id}/imports/")
    assert storage.objects[repository.jobs[0].source_object_key] == b"Name,Score\nAli,4\n"
    assert repository.audit_logs[0].action == "IMPORT_UPLOADED"


@pytest.mark.asyncio
async def test_permission_and_cross_workspace_profile_are_rejected() -> None:
    actor = identity()
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    import_service, _, _ = service(actor, workspace)
    with pytest.raises(PermissionDeniedError):
        await import_service.upload_and_inspect(
            workspace.id,
            ImportUpload("people.csv", "text/csv", BytesIO(b"Name\nAli\n"), None),
            audit=audit(),
        )

    authorized = identity(PermissionCode.IMPORT_EXECUTE)
    foreign_profile = ImportProfile(
        id=uuid4(),
        workspace_id=uuid4(),
        entity_type_id=uuid4(),
        name="Foreign",
        source_type="CSV",
        matching_strategy={"type": "ENTITY_ID", "source_column": "ID"},
        configuration={},
        created_by=authorized.user.id,
    )
    import_service, repository, storage = service(authorized, workspace, foreign_profile)
    with pytest.raises(ResourceNotFoundError):
        await import_service.upload_and_inspect(
            workspace.id,
            ImportUpload(
                "people.csv",
                "text/csv",
                BytesIO(b"Name\nAli\n"),
                foreign_profile.id,
            ),
            audit=audit(),
        )
    assert repository.jobs == []
    assert storage.objects == {}
