"""Credentials for authentication strategies."""

from __future__ import annotations

from dataclasses import dataclass


class Credentials:
    """Marker base class for auth credentials."""


@dataclass(slots=True)
class UsernamePasswordCredentials(Credentials):
    """Credentials using username and password."""

    username: str
    password: str


@dataclass(slots=True)
class TokenCredentials(Credentials):
    """Credentials using an (API) token."""

    token: str


@dataclass(slots=True)
class LocalTokenCredentials(TokenCredentials):
    """Credentials using a local API token."""


@dataclass(slots=True)
class RexelOAuthCodeCredentials(Credentials):
    """Credentials using Rexel OAuth2 authorization code."""

    code: str
    redirect_uri: str
