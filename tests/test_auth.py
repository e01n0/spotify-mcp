"""Tests for spotify_mcp.auth — PKCE primitives and OAuth flow."""

from __future__ import annotations

import base64
import hashlib
import re

from spotify_mcp.auth import PKCEFlow

PKCE_UNRESERVED = re.compile(r"^[A-Za-z0-9\-._~]+$")


def test_pkce_code_verifier_meets_rfc7636_spec() -> None:
    verifier = PKCEFlow.generate_verifier()
    assert 43 <= len(verifier) <= 128
    assert PKCE_UNRESERVED.match(verifier), f"verifier has reserved chars: {verifier!r}"


def test_pkce_code_verifier_is_unique_per_call() -> None:
    # Cryptographic randomness: collisions across 100 calls = effectively zero.
    samples = {PKCEFlow.generate_verifier() for _ in range(100)}
    assert len(samples) == 100


def test_pkce_code_challenge_is_s256_of_verifier() -> None:
    verifier = "test_verifier_with_enough_entropy_to_be_valid_xx"
    expected = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    assert PKCEFlow.challenge_for(verifier) == expected
    # And explicitly: no padding chars.
    assert "=" not in PKCEFlow.challenge_for(verifier)
