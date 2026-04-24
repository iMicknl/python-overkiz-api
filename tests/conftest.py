"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest_asyncio

from pyoverkiz.auth.credentials import (
    LocalTokenCredentials,
    UsernamePasswordCredentials,
)
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server
from pyoverkiz.utils import create_local_server_config


@pytest_asyncio.fixture
async def client() -> OverkizClient:
    """Fixture providing an OverkizClient configured for the cloud server."""
    return OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("username", "password"),
    )


@pytest_asyncio.fixture
async def local_client() -> OverkizClient:
    """Fixture providing an OverkizClient configured for a local (developer) server."""
    return OverkizClient(
        server=create_local_server_config(host="gateway-1234-5678-1243.local:8443"),
        credentials=LocalTokenCredentials(token="token"),  # noqa: S106
    )
