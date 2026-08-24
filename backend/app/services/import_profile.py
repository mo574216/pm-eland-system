"""Authorization and validation for reusable import profiles."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidMetadataError,
    PermissionDeniedError,
    ResourceNotFoundError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog
from app.models.import_job import ImportMapping, ImportProfile
from app.repositories.import_profile import ImportProfileRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.import_profile import (
    MATCHING_STRATEGY_ADAPTER,
    AttributeMatchKey,
    CompositeMatchingStrategy,
    ImportMappingInput,
    ImportMatchingStrategy,
    ParentKeyMatchingStrategy,
    UniqueAttributeMatchingStrategy,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService


@dataclass(frozen=True, slots=True)
class ImportProfileRecord:
    profile: ImportProfile
    mappings: tuple[ImportMapping, ...]


class ImportProfileService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = ImportProfileRepository(session)
        self.workspace_repository = WorkspaceRepository(session)

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

    async def _validate_targets(
        self, workspace_id: UUID, entity_type_id: UUID, mappings: tuple[ImportMappingInput, ...]
    ) -> None:
        if await self.repository.entity_type_in_workspace(entity_type_id, workspace_id) is None:
            raise InvalidMetadataError(
                {"field": "entity_type_id", "reason": "wrong_workspace_or_inactive"}
            )
        attribute_ids = frozenset(
            item.target_attribute_definition_id
            for item in mappings
            if item.target_attribute_definition_id is not None
        )
        attributes = await self.repository.active_attributes(entity_type_id, attribute_ids)
        if {item.id for item in attributes} != attribute_ids:
            raise InvalidMetadataError({"field": "mappings", "reason": "invalid_attribute_target"})
        sources = [(item.source_sheet, item.source_column) for item in mappings]
        if len(set(sources)) != len(sources):
            raise InvalidMetadataError({"field": "mappings", "reason": "duplicate_source_column"})

    @staticmethod
    def _matching_keys(strategy: ImportMatchingStrategy) -> tuple[AttributeMatchKey, ...]:
        if isinstance(strategy, UniqueAttributeMatchingStrategy):
            return (strategy.key,)
        if isinstance(strategy, CompositeMatchingStrategy):
            return strategy.keys
        if isinstance(strategy, ParentKeyMatchingStrategy):
            return (strategy.key,)
        return ()

    async def _validate_matching_strategy(
        self,
        entity_type_id: UUID,
        mappings: tuple[ImportMappingInput, ...],
        strategy: ImportMatchingStrategy,
    ) -> None:
        keys = self._matching_keys(strategy)
        attribute_ids = frozenset(
            key.attribute_definition_id for key in keys if key.attribute_definition_id is not None
        )
        attributes = await self.repository.active_attributes(entity_type_id, attribute_ids)
        if {attribute.id for attribute in attributes} != attribute_ids:
            raise InvalidMetadataError(
                {"field": "matching_strategy", "reason": "invalid_attribute_target"}
            )
        mapped_targets = {
            (
                mapping.source_sheet,
                mapping.source_column,
                mapping.target_attribute_definition_id,
                mapping.target_system_field,
            )
            for mapping in mappings
        }
        for key in keys:
            expected = (
                key.source_sheet,
                key.source_column,
                key.attribute_definition_id,
                key.system_field,
            )
            if expected not in mapped_targets:
                raise InvalidMetadataError(
                    {"field": "matching_strategy", "reason": "key_not_mapped"}
                )
        if isinstance(strategy, ParentKeyMatchingStrategy):
            parent_target = (
                strategy.parent_source_sheet,
                strategy.parent_source_column,
                None,
                "parent_id",
            )
            if parent_target not in mapped_targets:
                raise InvalidMetadataError(
                    {"field": "matching_strategy", "reason": "parent_not_mapped"}
                )

    def _audit(
        self,
        profile: ImportProfile,
        action: str,
        before: dict[str, object] | None,
        after: dict[str, object],
        audit: AuditContext,
    ) -> AuditLog:
        return AuditLog(
            id=uuid4(),
            request_id=audit.request_id,
            workspace_id=profile.workspace_id,
            user_id=self.actor.user.id,
            action=action,
            resource_type="import_profile",
            resource_id=profile.id,
            before_state=before,
            after_state=after,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )

    @staticmethod
    def _state(profile: ImportProfile, mappings: tuple[ImportMapping, ...]) -> dict[str, object]:
        return {
            "entity_type_id": str(profile.entity_type_id),
            "name": profile.name,
            "description": profile.description,
            "source_type": profile.source_type,
            "matching_strategy": profile.matching_strategy,
            "configuration": profile.configuration,
            "mappings": [
                {
                    "source_sheet": item.source_sheet,
                    "source_column": item.source_column,
                    "target_attribute_definition_id": str(item.target_attribute_definition_id)
                    if item.target_attribute_definition_id
                    else None,
                    "target_system_field": item.target_system_field,
                    "transformation_config": item.transformation_config,
                    "display_order": item.display_order,
                }
                for item in mappings
            ],
        }

    def _new_mappings(
        self, profile_id: UUID, values: tuple[ImportMappingInput, ...]
    ) -> tuple[ImportMapping, ...]:
        return tuple(
            ImportMapping(id=uuid4(), import_profile_id=profile_id, **item.model_dump())
            for item in values
        )

    async def create_profile(
        self,
        workspace_id: UUID,
        *,
        entity_type_id: UUID,
        name: str,
        description: str | None,
        source_type: str,
        matching_strategy: ImportMatchingStrategy,
        configuration: dict[str, object],
        mappings: tuple[ImportMappingInput, ...],
        audit: AuditContext,
    ) -> ImportProfileRecord:
        async with self.session.begin():
            await self._require_execute(workspace_id)
            await self._validate_targets(workspace_id, entity_type_id, mappings)
            await self._validate_matching_strategy(entity_type_id, mappings, matching_strategy)
            profile = ImportProfile(
                id=uuid4(),
                workspace_id=workspace_id,
                entity_type_id=entity_type_id,
                name=name,
                description=description,
                source_type=source_type,
                matching_strategy=matching_strategy.model_dump(mode="json"),
                configuration=configuration,
                created_by=self.actor.user.id,
            )
            created_mappings = self._new_mappings(profile.id, mappings)
            self.repository.add_profile(profile)
            for mapping in created_mappings:
                self.repository.add_mapping(mapping)
            self.repository.add_audit_log(
                self._audit(
                    profile,
                    "IMPORT_PROFILE_CREATED",
                    None,
                    self._state(profile, created_mappings),
                    audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as error:
                raise InvalidMetadataError(
                    {"field": "mappings", "reason": "invalid_reference"}
                ) from error
        return ImportProfileRecord(profile, created_mappings)

    async def get_profile(self, profile_id: UUID) -> ImportProfileRecord:
        profile = await self.repository.accessible_profile(profile_id, self.actor.user.id)
        if profile is None:
            raise ResourceNotFoundError
        await self._require_execute(profile.workspace_id)
        return ImportProfileRecord(profile, await self.repository.mappings(profile.id))

    async def list_profiles(
        self, workspace_id: UUID, *, page: int, page_size: int
    ) -> tuple[tuple[ImportProfileRecord, ...], int]:
        await self._require_execute(workspace_id)
        profiles, total = await self.repository.list_profiles(
            workspace_id, self.actor.user.id, page=page, page_size=page_size
        )
        records: list[ImportProfileRecord] = []
        for profile in profiles:
            records.append(ImportProfileRecord(profile, await self.repository.mappings(profile.id)))
        return tuple(records), total

    async def update_profile(
        self,
        profile_id: UUID,
        *,
        values: dict[str, object],
        mappings: tuple[ImportMappingInput, ...] | None,
        matching_strategy: ImportMatchingStrategy | None,
        audit: AuditContext,
    ) -> ImportProfileRecord:
        async with self.session.begin():
            profile = await self.repository.accessible_profile(profile_id, self.actor.user.id)
            if profile is None:
                raise ResourceNotFoundError
            await self._require_execute(profile.workspace_id)
            current = await self.repository.mappings(profile.id)
            before = self._state(profile, current)
            effective_mappings = mappings
            if effective_mappings is None:
                effective_mappings = tuple(
                    ImportMappingInput.model_validate(
                        {
                            "source_sheet": item.source_sheet,
                            "source_column": item.source_column,
                            "target_attribute_definition_id": item.target_attribute_definition_id,
                            "target_system_field": item.target_system_field,
                            "transformation_config": item.transformation_config,
                            "display_order": item.display_order,
                        }
                    )
                    for item in current
                )
            if matching_strategy is not None:
                await self._validate_matching_strategy(
                    profile.entity_type_id,
                    effective_mappings,
                    matching_strategy,
                )
                profile.matching_strategy = matching_strategy.model_dump(mode="json")
            if mappings is not None:
                await self._validate_targets(profile.workspace_id, profile.entity_type_id, mappings)
                if matching_strategy is None:
                    existing_strategy = MATCHING_STRATEGY_ADAPTER.validate_python(
                        profile.matching_strategy
                    )
                    await self._validate_matching_strategy(
                        profile.entity_type_id,
                        mappings,
                        existing_strategy,
                    )
                await self.repository.replace_mappings(profile.id)
                current = self._new_mappings(profile.id, mappings)
                for mapping in current:
                    self.repository.add_mapping(mapping)
            for key, value in values.items():
                setattr(profile, key, value)
            profile.updated_at = datetime.now(UTC)
            self.repository.add_audit_log(
                self._audit(
                    profile, "IMPORT_PROFILE_UPDATED", before, self._state(profile, current), audit
                )
            )
            await self.repository.flush()
        return ImportProfileRecord(profile, current)
