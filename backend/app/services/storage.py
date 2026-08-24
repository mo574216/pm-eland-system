"""Private object-storage boundary and MinIO adapter."""

import asyncio
from collections.abc import Callable
from datetime import timedelta
from functools import partial
from io import BytesIO
from typing import BinaryIO, Protocol, cast

from minio import Minio
from minio.error import S3Error

from app.core.config import Settings


class StorageError(RuntimeError):
    """Raised when private object storage cannot satisfy an operation."""


class StorageProvider(Protocol):
    """Async boundary used by document business services."""

    async def put_object(
        self, object_key: str, data: BinaryIO, *, length: int, content_type: str
    ) -> None: ...

    async def delete_object(self, object_key: str) -> None: ...

    async def object_exists(self, object_key: str) -> bool: ...

    async def read_object(self, object_key: str) -> bytes: ...

    async def create_download_url(self, object_key: str) -> str: ...

    async def create_upload_url(self, object_key: str) -> str: ...


class MinioStorageProvider:
    """MinIO implementation that keeps buckets private and URLs short-lived."""

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool,
        presigned_expiry_seconds: int = 600,
        client: Minio | None = None,
    ) -> None:
        if not 60 <= presigned_expiry_seconds <= 900:
            raise ValueError("Presigned URL expiry must be between 60 and 900 seconds.")
        if not bucket or "/" in bucket:
            raise ValueError("A valid private bucket name is required.")
        self._bucket = bucket
        self._expiry = timedelta(seconds=presigned_expiry_seconds)
        self._client = client or Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    async def ensure_bucket(self) -> None:
        """Create the configured private bucket when it does not exist."""
        try:
            exists = await self._call(self._client.bucket_exists, self._bucket)
            if not exists:
                await self._call(self._client.make_bucket, self._bucket)
        except S3Error as error:
            raise StorageError("Object-storage bucket initialization failed.") from error

    async def put_object(
        self, object_key: str, data: BinaryIO, *, length: int, content_type: str
    ) -> None:
        key = self._validated_key(object_key)
        if length < 0:
            raise ValueError("Object length cannot be negative.")
        try:
            await self._call(
                self._client.put_object,
                self._bucket,
                key,
                data,
                length,
                content_type=content_type,
            )
        except S3Error as error:
            raise StorageError("Object upload failed.") from error

    async def delete_object(self, object_key: str) -> None:
        key = self._validated_key(object_key)
        try:
            await self._call(self._client.remove_object, self._bucket, key)
        except S3Error as error:
            raise StorageError("Object deletion failed.") from error

    async def object_exists(self, object_key: str) -> bool:
        key = self._validated_key(object_key)
        try:
            await self._call(self._client.stat_object, self._bucket, key)
        except S3Error as error:
            if error.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                return False
            raise StorageError("Object lookup failed.") from error
        return True

    async def read_object(self, object_key: str) -> bytes:
        key = self._validated_key(object_key)
        response: object | None = None
        try:
            response = await self._call(self._client.get_object, self._bucket, key)
            reader = cast(BinaryIO, response)
            return cast(bytes, await self._call(reader.read))
        except S3Error as error:
            raise StorageError("Object read failed.") from error
        finally:
            if response is not None:
                close = getattr(response, "close", None)
                release_conn = getattr(response, "release_conn", None)
                if callable(close):
                    close()
                if callable(release_conn):
                    release_conn()

    async def create_download_url(self, object_key: str) -> str:
        key = self._validated_key(object_key)
        try:
            result = await self._call(
                self._client.presigned_get_object,
                self._bucket,
                key,
                expires=self._expiry,
            )
        except S3Error as error:
            raise StorageError("Download access generation failed.") from error
        return cast(str, result)

    async def create_upload_url(self, object_key: str) -> str:
        key = self._validated_key(object_key)
        try:
            result = await self._call(
                self._client.presigned_put_object,
                self._bucket,
                key,
                expires=self._expiry,
            )
        except S3Error as error:
            raise StorageError("Upload access generation failed.") from error
        return cast(str, result)

    @staticmethod
    async def _call(function: Callable[..., object], *args: object, **kwargs: object) -> object:
        return await asyncio.to_thread(partial(function, *args, **kwargs))

    @staticmethod
    def _validated_key(object_key: str) -> str:
        if (
            not object_key
            or object_key.startswith("/")
            or "\\" in object_key
            or any(part in {"", ".", ".."} for part in object_key.split("/"))
        ):
            raise ValueError("Object key must be a server-generated relative key.")
        return object_key


def in_memory_stream(value: bytes) -> BinaryIO:
    """Return a binary stream suitable for StorageProvider uploads."""
    return BytesIO(value)


def create_storage_provider(settings: Settings) -> StorageProvider:
    """Build the configured private storage adapter without exposing credentials."""
    if settings.storage_access_key is None or settings.storage_secret_key is None:
        raise RuntimeError("Object-storage credentials are not configured.")
    return MinioStorageProvider(
        endpoint=settings.storage_endpoint,
        access_key=settings.storage_access_key.get_secret_value(),
        secret_key=settings.storage_secret_key.get_secret_value(),
        bucket=settings.storage_bucket,
        secure=settings.storage_secure,
        presigned_expiry_seconds=settings.storage_presigned_expiry_seconds,
    )
