"""Readiness dependency contracts."""

from collections.abc import Awaitable, Callable

DatabaseProbe = Callable[[], Awaitable[bool]]
