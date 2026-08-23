"""Document persistence operations without transaction ownership."""

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.document import Document, DocumentVersion
from app.models.identity import AuditLog
from app.models.workspace import WorkspaceMembership


@dataclass(frozen=True)
class DocumentVersionRecord:
    version: DocumentVersion
    document: Document


@dataclass(frozen=True)
class DocumentRecord:
    document: Document
    current_version: DocumentVersion | None


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_document(self, document: Document) -> None:
        self.session.add(document)

    def add_version(self, version: DocumentVersion) -> None:
        self.session.add(version)

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self.session.add(audit_log)

    async def flush(self) -> None:
        await self.session.flush()

    async def lock_accessible_document(self, document_id: UUID, user_id: UUID) -> Document | None:
        statement = (
            select(Document)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == Document.workspace_id,
            )
            .where(
                Document.id == document_id,
                Document.lifecycle_status == "ACTIVE",
                Document.deleted_at.is_(None),
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
            .with_for_update(of=Document)
        )
        return cast(Document | None, await self.session.scalar(statement))

    async def next_version_number(self, document_id: UUID) -> int:
        current = await self.session.scalar(
            select(func.max(DocumentVersion.version_number)).where(
                DocumentVersion.document_id == document_id
            )
        )
        return int(current or 0) + 1

    async def accessible_version(
        self, version_id: UUID, user_id: UUID
    ) -> DocumentVersionRecord | None:
        statement = (
            select(DocumentVersion, Document)
            .join(Document, Document.id == DocumentVersion.document_id)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == Document.workspace_id,
            )
            .where(
                DocumentVersion.id == version_id,
                Document.lifecycle_status == "ACTIVE",
                Document.deleted_at.is_(None),
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        row = (await self.session.execute(statement)).one_or_none()
        if row is None:
            return None
        return DocumentVersionRecord(
            version=cast(DocumentVersion, row[0]),
            document=cast(Document, row[1]),
        )

    async def list_entity_documents(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[tuple[DocumentRecord, ...], int]:
        current = aliased(DocumentVersion)
        filters = (
            Document.workspace_id == workspace_id,
            Document.entity_id == entity_id,
            Document.lifecycle_status != "DELETED",
            Document.deleted_at.is_(None),
        )
        statement = (
            select(Document, current)
            .outerjoin(current, current.id == Document.current_version_id)
            .where(*filters)
            .order_by(Document.updated_at.desc(), Document.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(statement)).all()
        total = int(
            (await self.session.scalar(select(func.count(Document.id)).where(*filters))) or 0
        )
        return (
            tuple(
                DocumentRecord(cast(Document, row[0]), cast(DocumentVersion | None, row[1]))
                for row in rows
            ),
            total,
        )

    async def accessible_document_record(
        self, document_id: UUID, user_id: UUID
    ) -> DocumentRecord | None:
        current = aliased(DocumentVersion)
        statement = (
            select(Document, current)
            .outerjoin(current, current.id == Document.current_version_id)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == Document.workspace_id,
            )
            .where(
                Document.id == document_id,
                Document.lifecycle_status != "DELETED",
                Document.deleted_at.is_(None),
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        row = (await self.session.execute(statement)).one_or_none()
        if row is None:
            return None
        return DocumentRecord(
            cast(Document, row[0]),
            cast(DocumentVersion | None, row[1]),
        )

    async def list_versions(
        self, document_id: UUID, *, page: int, page_size: int
    ) -> tuple[tuple[DocumentVersion, ...], int]:
        filters = (DocumentVersion.document_id == document_id,)
        items = tuple(
            (
                await self.session.scalars(
                    select(DocumentVersion)
                    .where(*filters)
                    .order_by(DocumentVersion.version_number.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ).all()
        )
        total = int(
            (await self.session.scalar(select(func.count(DocumentVersion.id)).where(*filters))) or 0
        )
        return items, total
