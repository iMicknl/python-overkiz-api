"""Shared test helpers for the test suite."""

from __future__ import annotations

import json
from typing import Any, Self


class MockResponse:
    """Simple stand-in for aiohttp responses used in tests."""

    def __init__(self, text: str, status: int = 200, url: str = "") -> None:
        """Create a mock response with text payload and optional status/url."""
        self._text = text
        self.status = status
        self.url = url

    async def text(self) -> str:
        """Return text payload asynchronously."""
        return self._text

    async def json(self, content_type: str | None = None) -> Any:
        """Return parsed JSON payload asynchronously."""
        return json.loads(self._text)

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Context manager exit (noop)."""

    async def __aenter__(self) -> Self:
        """Context manager enter returning self."""
        return self
