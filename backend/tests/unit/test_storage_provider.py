"""Private object-storage abstraction tests."""

from datetime import timedelta
from io import BytesIO
from typing import cast

import pytest
from minio import Minio

from app.core.config import Settings
from app.services.storage import (
    MinioStorageProvider,
    StorageProvider,
    create_storage_provider,
)


class FakeMinio:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def _record(self, name: str, *args: object, **kwargs: object) -> None:
        self.calls.append((name, args, kwargs))

    def put_object(self, *args: object, **kwargs: object) -> object:
        self._record("put", *args, **kwargs)
        return object()

    def remove_object(self, *args: object, **kwargs: object) -> None:
        self._record("delete", *args, **kwargs)

    def stat_object(self, *args: object, **kwargs: object) -> object:
        self._record("stat", *args, **kwargs)
        return object()

    def get_object(self, *args: object, **kwargs: object) -> BytesIO:
        self._record("read", *args, **kwargs)
        response = BytesIO(b"private content")
        response.release_conn = lambda: None  # type: ignore[attr-defined]
        return response

    def presigned_get_object(self, *args: object, **kwargs: object) -> str:
        self._record("download", *args, **kwargs)
        return "https://storage.test/private-download"

    def presigned_put_object(self, *args: object, **kwargs: object) -> str:
        self._record("upload", *args, **kwargs)
        return "https://storage.test/private-upload"


def provider(fake: FakeMinio) -> MinioStorageProvider:
    return MinioStorageProvider(
        endpoint="storage.test",
        access_key="access",
        secret_key="secret",  # noqa: S106
        bucket="private-documents",
        secure=True,
        presigned_expiry_seconds=300,
        client=cast(Minio, fake),
    )


@pytest.mark.asyncio
async def test_adapter_uploads_to_private_bucket_and_scopes_short_lived_urls() -> None:
    fake = FakeMinio()
    storage: StorageProvider = provider(fake)

    await storage.put_object(
        "workspaces/generated-id/original",
        BytesIO(b"content"),
        length=7,
        content_type="application/pdf",
    )
    assert await storage.create_download_url("workspaces/generated-id/original") == (
        "https://storage.test/private-download"
    )
    assert await storage.create_upload_url("workspaces/generated-id/original") == (
        "https://storage.test/private-upload"
    )
    assert await storage.read_object("workspaces/generated-id/original") == b"private content"

    assert fake.calls[0][0:2] == (
        "put",
        ("private-documents", "workspaces/generated-id/original", fake.calls[0][1][2], 7),
    )
    assert fake.calls[0][2]["content_type"] == "application/pdf"
    assert fake.calls[1][2]["expires"] == timedelta(seconds=300)
    assert fake.calls[2][2]["expires"] == timedelta(seconds=300)
    assert fake.calls[3][0:2] == (
        "read",
        ("private-documents", "workspaces/generated-id/original"),
    )


@pytest.mark.asyncio
async def test_adapter_rejects_user_path_shapes_before_storage_access() -> None:
    fake = FakeMinio()
    storage = provider(fake)

    for unsafe in ("", "/absolute", "../escape", "folder/../escape", "folder\\escape"):
        with pytest.raises(ValueError, match="server-generated"):
            await storage.object_exists(unsafe)

    assert fake.calls == []


def test_factory_requires_secrets_and_settings_bound_url_expiry() -> None:
    with pytest.raises(RuntimeError, match="credentials"):
        create_storage_provider(Settings())
    with pytest.raises(ValueError, match="between 60 and 900"):
        MinioStorageProvider(
            endpoint="storage.test",
            access_key="access",
            secret_key="secret",  # noqa: S106
            bucket="private-documents",
            secure=True,
            presigned_expiry_seconds=901,
        )
