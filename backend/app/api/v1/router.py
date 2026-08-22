"""Base router for all version 1 public endpoints."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.entities import router as entities_router
from app.api.v1.metadata import router as metadata_router
from app.api.v1.users import router as users_router
from app.api.v1.workspaces import router as workspaces_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(entities_router)
api_router.include_router(metadata_router)
api_router.include_router(users_router)
api_router.include_router(workspaces_router)
