"""Reusable import-profile administration endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.request_context import get_request_id
from app.schemas.import_profile import (
    ImportMappingResponse,
    ImportProfileCreate,
    ImportProfileListResponse,
    ImportProfileResponse,
    ImportProfileUpdate,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.import_profile import ImportProfileRecord, ImportProfileService

router = APIRouter(tags=["Imports"])


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def _response(record: ImportProfileRecord) -> ImportProfileResponse:
    profile = record.profile
    return ImportProfileResponse(
        id=profile.id,
        workspace_id=profile.workspace_id,
        entity_type_id=profile.entity_type_id,
        name=profile.name,
        description=profile.description,
        source_type=profile.source_type,
        matching_strategy=profile.matching_strategy,
        configuration=profile.configuration,
        created_by=profile.created_by,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        mappings=tuple(ImportMappingResponse.model_validate(item) for item in record.mappings),
    )


@router.post(
    "/workspaces/{workspace_id}/import-profiles",
    status_code=status.HTTP_201_CREATED,
)
async def create_import_profile(
    workspace_id: UUID,
    payload: ImportProfileCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    record = await ImportProfileService(session, actor).create_profile(
        workspace_id,
        entity_type_id=payload.entity_type_id,
        name=payload.name,
        description=payload.description,
        source_type=payload.source_type,
        configuration=payload.configuration,
        mappings=payload.mappings,
        audit=_audit_context(request),
    )
    return success_envelope(_response(record).model_dump(mode="json"))


@router.get("/workspaces/{workspace_id}/import-profiles")
async def list_import_profiles(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, object]:
    records, total = await ImportProfileService(session, actor).list_profiles(
        workspace_id, page=page, page_size=page_size
    )
    result = ImportProfileListResponse(
        items=tuple(_response(record) for record in records),
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_envelope(result.model_dump(mode="json"))


@router.get("/import-profiles/{profile_id}")
async def get_import_profile(
    profile_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    record = await ImportProfileService(session, actor).get_profile(profile_id)
    return success_envelope(_response(record).model_dump(mode="json"))


@router.patch("/import-profiles/{profile_id}")
async def update_import_profile(
    profile_id: UUID,
    payload: ImportProfileUpdate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    dumped = payload.model_dump(exclude={"mappings"}, exclude_unset=True)
    record = await ImportProfileService(session, actor).update_profile(
        profile_id,
        values=dumped,
        mappings=payload.mappings if "mappings" in payload.model_fields_set else None,
        audit=_audit_context(request),
    )
    return success_envelope(_response(record).model_dump(mode="json"))
