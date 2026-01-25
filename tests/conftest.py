"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import json

import pytest_asyncio

from pyoverkiz.client import OverkizClient
from pyoverkiz.const import SUPPORTED_SERVERS
from pyoverkiz.utils import generate_local_server


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

    async def json(self, content_type: str | None = None) -> dict:
        """Return parsed JSON payload asynchronously."""
        return json.loads(self._text)

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Context manager exit (noop)."""
        pass

    async def __aenter__(self) -> MockResponse:
        """Context manager enter returning self."""
        return self


@pytest_asyncio.fixture
async def client() -> OverkizClient:
    """Fixture providing an OverkizClient configured for the cloud server."""
    return OverkizClient("username", "password", SUPPORTED_SERVERS["somfy_europe"])


@pytest_asyncio.fixture
async def local_client() -> OverkizClient:
    """Fixture providing an OverkizClient configured for a local (developer) server."""
    return OverkizClient(
        "username",
        "password",
        generate_local_server("gateway-1234-5678-1243.local:8443"),
    )
