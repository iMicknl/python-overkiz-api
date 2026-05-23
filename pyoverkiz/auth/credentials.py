"""Credentials for authentication strategies."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field


class Credentials(ABC):  # noqa: B024 - marker class uses ABC to prevent direct instantiation
    """Abstract base class for auth credentials."""


@dataclass(slots=True)
class UsernamePasswordCredentials(Credentials):
    """Credentials using username and password."""

    username: str
    password: str = field(repr=False)


@dataclass(slots=True)
class TokenCredentials(Credentials):
    """Credentials using an (API) token."""

    token: str = field(repr=False)


@dataclass(slots=True)
class LocalTokenCredentials(TokenCredentials):
    """Credentials using a local API token."""


@dataclass(slots=True)
class RexelOAuthCodeCredentials(Credentials):
    """Credentials using Rexel OAuth2 authorization code."""

    code: str = field(repr=False)
    redirect_uri: str
