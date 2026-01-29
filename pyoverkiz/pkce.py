"""Utilities for OAuth2 PKCE (Proof Key for Code Exchange) flow."""

from __future__ import annotations

import base64
import hashlib
import secrets


def generate_code_verifier(length: int = 64) -> str:
    """Generate a cryptographically random code verifier for PKCE.

    The code verifier is a high-entropy cryptographic random string using
    unreserved characters [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~",
    with a minimum length of 43 characters and a maximum length of 128.

    Args:
        length: Number of random bytes to generate (default 64, resulting in ~86 chars)

    Returns:
        Base64 URL-safe encoded string without padding
    """
    if length < 32 or length > 96:
        raise ValueError("Length must be between 32 and 96 bytes")

    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(length)).decode(
        "utf-8"
    )
    # Remove padding as per RFC 7636
    return code_verifier.rstrip("=")


def generate_code_challenge(code_verifier: str) -> str:
    """Generate the code challenge from a code verifier using S256 method.

    As per RFC 7636, the code challenge is the Base64 URL-encoded SHA-256
    hash of the code verifier.

    Args:
        code_verifier: The code verifier string

    Returns:
        Base64 URL-safe encoded SHA-256 hash without padding
    """
    code_challenge_bytes = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge_bytes).decode("utf-8")
    # Remove padding as per RFC 7636
    return code_challenge.rstrip("=")


def generate_pkce_pair(verifier_length: int = 64) -> tuple[str, str]:
    """Generate both PKCE code verifier and code challenge.

    Args:
        verifier_length: Number of random bytes for the verifier (default 64)

    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    code_verifier = generate_code_verifier(verifier_length)
    code_challenge = generate_code_challenge(code_verifier)
    return code_verifier, code_challenge
