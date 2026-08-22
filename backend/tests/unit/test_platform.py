"""Platform compatibility tests."""

import asyncio
import sys

import pytest

import app.main  # noqa: F401


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific event-loop policy")
def test_windows_uses_selector_event_loop_policy_for_psycopg() -> None:
    selector_policy_type = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)

    assert selector_policy_type is not None
    assert isinstance(asyncio.get_event_loop_policy(), selector_policy_type)
