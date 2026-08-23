"""Typed environment configuration."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or local dotenv files."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    log_level: str = "INFO"
    docs_enabled: bool = True
    database_url: str | None = None
    database_echo: bool = False
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_connect_timeout_seconds: int = Field(default=5, ge=1, le=30)
    jwt_secret: SecretStr | None = Field(default=None, min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_issuer: str = "pm-eland-system"
    jwt_audience: str = "pm-eland-api"
    jwt_expiry_seconds: int = Field(default=900, ge=60, le=3600)
    refresh_idle_expiry_seconds: int = Field(default=604800, ge=300)
    refresh_absolute_expiry_seconds: int = Field(default=2592000, ge=3600)
    auth_cookie_secure: bool = True
    auth_cookie_name: str = "__Host-pm_refresh"
    cors_origins: list[AnyHttpUrl] = Field(
        default_factory=lambda: [AnyHttpUrl("http://localhost:5173")]
    )
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )
    storage_endpoint: str = "localhost:9000"
    storage_access_key: SecretStr | None = None
    storage_secret_key: SecretStr | None = None
    storage_secure: bool = False
    storage_bucket: str = "pm-eland-documents"
    storage_presigned_expiry_seconds: int = Field(default=600, ge=60, le=900)

    @model_validator(mode="after")
    def validate_authentication_security(self) -> Self:
        if self.refresh_absolute_expiry_seconds < self.refresh_idle_expiry_seconds:
            raise ValueError("Refresh absolute expiry must not be shorter than idle expiry.")
        if self.app_env.lower() == "production":
            if self.jwt_secret is None:
                raise ValueError("JWT_SECRET is required in production.")
            if not self.auth_cookie_secure:
                raise ValueError("AUTH_COOKIE_SECURE must be enabled in production.")
            if self.storage_access_key is None or self.storage_secret_key is None:
                raise ValueError("Object-storage credentials are required in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-level settings instance."""
    return Settings()
