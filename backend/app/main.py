"""FastAPI application factory and default ASGI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.error_handlers import register_error_handlers
from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import (
    check_database_connection,
    create_database_engine,
    create_session_factory,
)
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.readiness import DatabaseProbe


def create_app(
    settings: Settings | None = None,
    *,
    database_probe: DatabaseProbe | None = None,
) -> FastAPI:
    """Build an application instance with explicit, testable dependencies."""
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(lifespan_app: FastAPI) -> AsyncIterator[None]:
        configure_logging(resolved_settings.log_level)
        engine = None
        if resolved_settings.database_url is not None:
            engine = create_database_engine(
                resolved_settings.database_url,
                echo=resolved_settings.database_echo,
                pool_size=resolved_settings.database_pool_size,
                max_overflow=resolved_settings.database_max_overflow,
                connect_timeout_seconds=resolved_settings.database_connect_timeout_seconds,
            )
            lifespan_app.state.database_engine = engine
            lifespan_app.state.session_factory = create_session_factory(engine)
            lifespan_app.state.database_probe = database_probe or partial(
                check_database_connection, engine
            )
        try:
            yield
        finally:
            if engine is not None:
                await engine.dispose()

    application = FastAPI(
        title="Project Knowledge Platform API",
        version="0.1.0",
        openapi_version="3.1.0",
        docs_url="/docs" if resolved_settings.docs_enabled else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.state.database_engine = None
    application.state.session_factory = None
    application.state.database_probe = database_probe

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in resolved_settings.cors_origins],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "If-Match", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=resolved_settings.allowed_hosts,
    )
    application.add_middleware(RequestContextMiddleware)

    register_error_handlers(application)
    application.include_router(health_router)
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
