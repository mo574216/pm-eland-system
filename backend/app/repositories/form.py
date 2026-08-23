"""Workspace-isolated form definition persistence operations."""

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.form import FormDefinition, FormField
from app.models.identity import AuditLog
from app.models.metadata import AttributeDefinition, EntityType
from app.models.workspace import WorkspaceMembership


@dataclass(frozen=True)
class FormRecord:
    form: FormDefinition
    fields: tuple[FormField, ...]


class FormRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_form(self, value: FormDefinition) -> None:
        self.session.add(value)

    def add_field(self, value: FormField) -> None:
        self.session.add(value)

    def add_audit_log(self, value: AuditLog) -> None:
        self.session.add(value)

    async def flush(self) -> None:
        await self.session.flush()

    async def form_by_key(self, workspace_id: UUID, key: str) -> FormDefinition | None:
        statement = select(FormDefinition).where(
            FormDefinition.workspace_id == workspace_id,
            FormDefinition.key == key,
        )
        return cast(FormDefinition | None, await self.session.scalar(statement))

    async def entity_type_in_workspace(
        self, entity_type_id: UUID, workspace_id: UUID
    ) -> EntityType | None:
        statement = select(EntityType).where(
            EntityType.id == entity_type_id,
            EntityType.workspace_id == workspace_id,
            EntityType.deleted_at.is_(None),
            EntityType.is_active.is_(True),
        )
        return cast(EntityType | None, await self.session.scalar(statement))

    async def list_forms(
        self,
        workspace_id: UUID,
        user_id: UUID,
        *,
        entity_type_id: UUID | None,
        lifecycle_status: str | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> tuple[tuple[FormDefinition, ...], int]:
        filters = [
            FormDefinition.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.status == "ACTIVE",
        ]
        if entity_type_id is not None:
            filters.append(FormDefinition.entity_type_id == entity_type_id)
        if lifecycle_status is not None:
            filters.append(FormDefinition.lifecycle_status == lifecycle_status)
        if search is not None:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    FormDefinition.key.ilike(pattern),
                    FormDefinition.name.ilike(pattern),
                    FormDefinition.description.ilike(pattern),
                )
            )
        join = WorkspaceMembership.workspace_id == FormDefinition.workspace_id
        statement = select(FormDefinition).join(WorkspaceMembership, join)
        count_statement = select(func.count(FormDefinition.id)).join(WorkspaceMembership, join)
        items = tuple(
            (
                await self.session.scalars(
                    statement.where(*filters)
                    .order_by(FormDefinition.name, FormDefinition.version_number.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ).all()
        )
        total = int((await self.session.scalar(count_statement.where(*filters))) or 0)
        return items, total

    async def accessible_form(self, form_id: UUID, user_id: UUID) -> FormDefinition | None:
        statement = (
            select(FormDefinition)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == FormDefinition.workspace_id,
            )
            .where(
                FormDefinition.id == form_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        return cast(FormDefinition | None, await self.session.scalar(statement))

    async def list_fields(self, form_id: UUID) -> tuple[FormField, ...]:
        statement = (
            select(FormField)
            .where(FormField.form_definition_id == form_id)
            .order_by(FormField.display_order, FormField.label, FormField.id)
        )
        return tuple((await self.session.scalars(statement)).all())

    async def accessible_form_record(self, form_id: UUID, user_id: UUID) -> FormRecord | None:
        form = await self.accessible_form(form_id, user_id)
        if form is None:
            return None
        return FormRecord(form, await self.list_fields(form_id))

    async def update_draft_form(
        self, form_id: UUID, values: dict[str, object]
    ) -> FormDefinition | None:
        statement = (
            update(FormDefinition)
            .where(
                FormDefinition.id == form_id,
                FormDefinition.lifecycle_status == "DRAFT",
            )
            .values(**values)
            .returning(FormDefinition)
        )
        return cast(FormDefinition | None, await self.session.scalar(statement))

    async def field_by_key(self, form_id: UUID, key: str) -> FormField | None:
        statement = select(FormField).where(
            FormField.form_definition_id == form_id,
            FormField.key == key,
        )
        return cast(FormField | None, await self.session.scalar(statement))

    async def attribute_in_workspace(
        self, attribute_id: UUID, workspace_id: UUID
    ) -> tuple[AttributeDefinition, EntityType] | None:
        statement = (
            select(AttributeDefinition, EntityType)
            .join(EntityType, EntityType.id == AttributeDefinition.entity_type_id)
            .where(
                AttributeDefinition.id == attribute_id,
                AttributeDefinition.deleted_at.is_(None),
                AttributeDefinition.is_active.is_(True),
                EntityType.workspace_id == workspace_id,
                EntityType.deleted_at.is_(None),
                EntityType.is_active.is_(True),
            )
        )
        row = (await self.session.execute(statement)).one_or_none()
        return None if row is None else cast(tuple[AttributeDefinition, EntityType], tuple(row))
