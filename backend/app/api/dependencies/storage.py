"""Object-storage dependency resolution."""

from typing import cast

from fastapi import Request

from app.services.storage import StorageProvider, create_storage_provider


def get_storage_provider(request: Request) -> StorageProvider:
    configured = request.app.state.storage_provider
    if configured is not None:
        return cast(StorageProvider, configured)
    return create_storage_provider(request.app.state.settings)
