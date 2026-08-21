"""Unversioned process health and dependency readiness endpoints."""

from typing import cast

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.envelopes import error_envelope, success_envelope
from app.core.config import Settings
from app.core.readiness import DatabaseProbe
from app.core.request_context import get_request_id

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, object]:
    """Report process viability without checking external dependencies."""
    return success_envelope({"status": "ok"})


@router.get("/ready", response_model=None)
async def readiness(request: Request) -> dict[str, object] | JSONResponse:
    """Fail closed when a configured critical dependency is unavailable."""
    settings = cast(Settings, request.app.state.settings)
    database_probe = cast(DatabaseProbe | None, request.app.state.database_probe)

    if settings.database_url is None:
        return success_envelope({"status": "ready", "checks": {"database": "not_configured"}})

    if database_probe is None or not await database_probe():
        request_id = get_request_id()
        return JSONResponse(
            status_code=503,
            content=error_envelope(
                code="DEPENDENCY_UNAVAILABLE",
                message="A required service is unavailable.",
                details={"checks": {"database": "unavailable"}},
                request_id=request_id,
            ),
            headers={"X-Request-ID": request_id},
        )

    return success_envelope({"status": "ready", "checks": {"database": "ok"}})
