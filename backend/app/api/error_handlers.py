"""Centralized mapping from application errors to safe HTTP responses."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.envelopes import error_envelope
from app.core.exceptions import ApplicationError
from app.core.localization import public_error_message
from app.core.request_context import get_request_id

logger = logging.getLogger(__name__)


def register_error_handlers(application: FastAPI) -> None:
    """Register stable error responses without exposing internal exceptions."""

    @application.exception_handler(ApplicationError)
    async def handle_application_error(_: Request, exc: ApplicationError) -> JSONResponse:
        request_id = get_request_id()
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(
                code=exc.code,
                message=exc.public_message,
                details=exc.details,
                request_id=request_id,
            ),
            headers={"X-Request-ID": request_id},
        )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        request_id = get_request_id()
        logger.exception(
            "unhandled_application_error", extra={"request_id": request_id}, exc_info=exc
        )
        return JSONResponse(
            status_code=500,
            content=error_envelope(
                code="INTERNAL_ERROR",
                message=public_error_message("INTERNAL_ERROR"),
                request_id=request_id,
            ),
            headers={"X-Request-ID": request_id},
        )
