"""Workspace-scoped generic entity persistence operations."""

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import String, and_, any_, exists, func, literal, select, update
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.elements import ColumnElement

from app.models.entity import EntityObject
from app.models.identity import AuditLog, User
from app.models.metadata import EntityType
from app.models.workspace import WorkspaceMembership


@dataclass(frozen=True)
class EntityRecord:
    entity: EntityObject
    entity_type: EntityType


@dataclass(frozen=True)
class EntityTreeRecord:
    id: UUID
    workspace_id: UUID
    entity_type_id: UUID
    parent_id: UUID | None
    name: str
    status: str
    depth: int
    path: tuple[UUID, ...]
    has_children: bool
    entity_type_key: str | None
    entity_type_name: str | None
    entity_type_icon_key: str | None


class EntityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_entity(self, entity: EntityObject) -> None:
        self.session.add(entity)

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self.session.add(audit_log)

    async def flush(self) -> None:
        await self.session.flush()

    async def entity_in_workspace(self, entity_id: UUID, workspace_id: UUID) -> EntityObject | None:
        statement = select(EntityObject).where(
            EntityObject.id == entity_id,
            EntityObject.workspace_id == workspace_id,
            EntityObject.deleted_at.is_(None),
        )
        return cast(EntityObject | None, await self.session.scalar(statement))

    async def user_reference_exists(self, user_id: UUID, workspace_id: UUID) -> bool:
        statement = (
            select(User.id)
            .join(WorkspaceMembership, WorkspaceMembership.user_id == User.id)
            .where(
                User.id == user_id,
                User.is_active.is_(True),
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        return await self.session.scalar(statement) is not None

    async def accessible_entity(self, entity_id: UUID, user_id: UUID) -> EntityObject | None:
        statement = (
            select(EntityObject)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == EntityObject.workspace_id,
            )
            .where(
                EntityObject.id == entity_id,
                EntityObject.deleted_at.is_(None),
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        return cast(EntityObject | None, await self.session.scalar(statement))

    async def accessible_entity_record(self, entity_id: UUID, user_id: UUID) -> EntityRecord | None:
        statement = (
            select(EntityObject, EntityType)
            .join(EntityType, EntityType.id == EntityObject.entity_type_id)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == EntityObject.workspace_id,
            )
            .where(
                EntityObject.id == entity_id,
                EntityObject.deleted_at.is_(None),
                EntityType.deleted_at.is_(None),
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        row = (await self.session.execute(statement)).one_or_none()
        if row is None:
            return None
        return EntityRecord(row[0], row[1])

    @staticmethod
    def _normalized_name_expression() -> ColumnElement[str]:
        translated = func.translate(
            EntityObject.name,
            "يىك٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
            "ییک01234567890123456789",
        )
        without_marks = func.regexp_replace(
            translated,
            "[\u064b-\u065f\u0670\u200c\u200d\u0640]",
            "",
            "g",
        )
        expression = func.lower(func.btrim(func.regexp_replace(without_marks, r"\s+", " ", "g")))
        return cast(ColumnElement[str], expression)

    async def list_entities(
        self,
        workspace_id: UUID,
        user_id: UUID,
        *,
        page: int,
        page_size: int,
        status: str | None,
        entity_type_id: UUID | None,
        parent_id: UUID | None,
        search: str | None,
    ) -> tuple[tuple[EntityRecord, ...], int]:
        filters = [
            EntityObject.workspace_id == workspace_id,
            EntityObject.deleted_at.is_(None),
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.status == "ACTIVE",
        ]
        if status is not None:
            filters.append(EntityObject.status == status)
        if entity_type_id is not None:
            filters.append(EntityObject.entity_type_id == entity_type_id)
        if parent_id is not None:
            filters.append(EntityObject.parent_id == parent_id)
        if search is not None:
            filters.append(self._normalized_name_expression().ilike(f"%{search}%"))
        join_condition = WorkspaceMembership.workspace_id == EntityObject.workspace_id
        statement = (
            select(EntityObject, EntityType)
            .join(EntityType, EntityType.id == EntityObject.entity_type_id)
            .join(WorkspaceMembership, join_condition)
        )
        count_statement = select(func.count(EntityObject.id)).join(
            WorkspaceMembership, join_condition
        )
        rows = (
            await self.session.execute(
                statement.where(*filters)
                .order_by(EntityObject.name, EntityObject.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        items = tuple(EntityRecord(entity, entity_type) for entity, entity_type in rows)
        total = int((await self.session.scalar(count_statement.where(*filters))) or 0)
        return items, total

    async def entity_tree(
        self,
        workspace_id: UUID,
        user_id: UUID,
        *,
        root_id: UUID | None,
        max_depth: int | None,
        include_type: bool,
    ) -> tuple[EntityTreeRecord, ...]:
        anchor_filters = [
            EntityObject.workspace_id == workspace_id,
            EntityObject.deleted_at.is_(None),
            EntityObject.status != "DELETED",
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.status == "ACTIVE",
        ]
        anchor_filters.append(
            EntityObject.id == root_id if root_id is not None else EntityObject.parent_id.is_(None)
        )
        anchor = (
            select(
                EntityObject.id.label("id"),
                EntityObject.workspace_id.label("workspace_id"),
                EntityObject.entity_type_id.label("entity_type_id"),
                EntityObject.parent_id.label("parent_id"),
                EntityObject.name.label("name"),
                EntityObject.status.label("status"),
                literal(0).label("depth"),
                array([EntityObject.id]).label("path"),
            )
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == EntityObject.workspace_id,
            )
            .where(*anchor_filters)
        )
        tree = anchor.cte("entity_tree", recursive=True)
        child = aliased(EntityObject, name="child")
        descendants = select(
            child.id,
            child.workspace_id,
            child.entity_type_id,
            child.parent_id,
            child.name,
            child.status,
            (tree.c.depth + 1).label("depth"),
            (tree.c.path + array([child.id])).label("path"),
        ).join(tree, child.parent_id == tree.c.id)
        descendants = descendants.where(
            child.workspace_id == workspace_id,
            child.workspace_id == tree.c.workspace_id,
            child.deleted_at.is_(None),
            child.status != "DELETED",
            ~(child.id == any_(tree.c.path)),
        )
        if max_depth is not None:
            descendants = descendants.where(tree.c.depth < max_depth)
        tree = tree.union_all(descendants)

        possible_child = aliased(EntityObject, name="possible_child")
        has_children = exists(
            select(possible_child.id).where(
                possible_child.parent_id == tree.c.id,
                possible_child.workspace_id == workspace_id,
                possible_child.deleted_at.is_(None),
                possible_child.status != "DELETED",
            )
        ).label("has_children")
        columns = [
            tree.c.id,
            tree.c.workspace_id,
            tree.c.entity_type_id,
            tree.c.parent_id,
            tree.c.name,
            tree.c.status,
            tree.c.depth,
            tree.c.path,
            has_children,
        ]
        if include_type:
            columns.extend(
                [
                    EntityType.key.label("entity_type_key"),
                    EntityType.name.label("entity_type_name"),
                    EntityType.icon_key.label("entity_type_icon_key"),
                ]
            )
            statement = select(*columns).outerjoin(
                EntityType,
                and_(
                    EntityType.id == tree.c.entity_type_id,
                    EntityType.workspace_id == workspace_id,
                    EntityType.deleted_at.is_(None),
                ),
            )
        else:
            columns.extend(
                [
                    literal(None).cast(String).label("entity_type_key"),
                    literal(None).cast(String).label("entity_type_name"),
                    literal(None).cast(String).label("entity_type_icon_key"),
                ]
            )
            statement = select(*columns)
        rows = (await self.session.execute(statement.order_by(tree.c.path))).mappings().all()
        return tuple(
            EntityTreeRecord(
                id=row["id"],
                workspace_id=row["workspace_id"],
                entity_type_id=row["entity_type_id"],
                parent_id=row["parent_id"],
                name=row["name"],
                status=row["status"],
                depth=int(row["depth"]),
                path=tuple(row["path"]),
                has_children=bool(row["has_children"]),
                entity_type_key=row["entity_type_key"],
                entity_type_name=row["entity_type_name"],
                entity_type_icon_key=row["entity_type_icon_key"],
            )
            for row in rows
        )

    async def update_entity(
        self, entity_id: UUID, expected_version: int, values: dict[str, object]
    ) -> EntityObject | None:
        statement = (
            update(EntityObject)
            .where(
                EntityObject.id == entity_id,
                EntityObject.version == expected_version,
                EntityObject.deleted_at.is_(None),
                EntityObject.status == "ACTIVE",
            )
            .values(
                **values,
                version=EntityObject.version + 1,
                updated_at=func.now(),
            )
            .returning(EntityObject)
        )
        return cast(EntityObject | None, await self.session.scalar(statement))

    async def archive_entity(
        self, entity_id: UUID, expected_version: int, updated_by: UUID
    ) -> EntityObject | None:
        return await self.update_entity(
            entity_id,
            expected_version,
            {"status": "ARCHIVED", "archived_at": func.now(), "updated_by": updated_by},
        )
