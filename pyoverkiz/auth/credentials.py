from __future__ import annotations

from dataclasses import dataclass


class Credentials:
    """Marker base class for auth credentials."""


@dataclass(slots=True)
class UsernamePasswordCredentials(Credentials):
    username: str
    password: str


@dataclass(slots=True)
class TokenCredentials(Credentials):
    token: str


@dataclass(slots=True)
class LocalTokenCredentials(TokenCredentials): ...


@dataclass(slots=True)
class RexelOAuthCodeCredentials(Credentials):
    code: str
    redirect_uri: str
