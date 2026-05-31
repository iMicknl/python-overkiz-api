"""Authentication module for pyoverkiz."""

from __future__ import annotations

from pyoverkiz.auth.base import (
    AuthContext,
    AuthStrategy,
    GatewayCandidate,
    SupportsGatewaySelection,
)
from pyoverkiz.auth.credentials import (
    Credentials,
    LocalTokenCredentials,
    RexelOAuthCodeCredentials,
    RexelTokenCredentials,
    TokenCredentials,
    UsernamePasswordCredentials,
)
from pyoverkiz.auth.factory import build_auth_strategy

__all__ = [
    "AuthContext",
    "AuthStrategy",
    "Credentials",
    "GatewayCandidate",
    "LocalTokenCredentials",
    "RexelOAuthCodeCredentials",
    "RexelTokenCredentials",
    "SupportsGatewaySelection",
    "TokenCredentials",
    "UsernamePasswordCredentials",
    "build_auth_strategy",
]
