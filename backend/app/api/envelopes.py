"""Standard API response envelope helpers."""

from typing import Any


def success_envelope(data: Any, *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the canonical successful JSON response shape."""
    return {"success": True, "data": data, "error": None, "meta": meta or {}}


def error_envelope(
    *,
    code: str,
    message: str,
    request_id: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the canonical failed JSON response shape."""
    return {
        "success": False,
        "data": None,
        "error": {"code": code, "message": message, "details": details or {}},
        "meta": {"request_id": request_id},
    }
