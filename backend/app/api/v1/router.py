"""Base router for all version 1 public endpoints."""

from fastapi import APIRouter

from app.api.v1.acceptance import router as acceptance_router
from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboards import router as dashboards_router
from app.api.v1.deliverables import router as deliverables_router
from app.api.v1.documents import router as documents_router
from app.api.v1.entities import router as entities_router
from app.api.v1.forms import router as forms_router
from app.api.v1.imports import router as imports_router
from app.api.v1.metadata import router as metadata_router
from app.api.v1.phases import router as phases_router
from app.api.v1.relationships import router as relationships_router
from app.api.v1.users import router as users_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.workspaces import router as workspaces_router

api_router = APIRouter()
api_router.include_router(acceptance_router)
api_router.include_router(audit_router)
api_router.include_router(auth_router)
api_router.include_router(dashboards_router)
api_router.include_router(deliverables_router)
api_router.include_router(documents_router)
api_router.include_router(entities_router)
api_router.include_router(forms_router)
api_router.include_router(imports_router)
api_router.include_router(metadata_router)
api_router.include_router(phases_router)
api_router.include_router(relationships_router)
api_router.include_router(users_router)
api_router.include_router(workspaces_router)
api_router.include_router(workflows_router)
