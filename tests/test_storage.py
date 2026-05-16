"""Tests for spotify_mcp.storage — keyring-backed refresh token persistence."""

from __future__ import annotations

import pytest

from spotify_mcp.storage import NoRefreshTokenError, Storage


def test_storage_raises_no_refresh_token_when_keyring_empty(
    fake_keyring: dict[tuple[str, str], str],
) -> None:
    storage = Storage(client_id="client_abc")
    with pytest.raises(NoRefreshTokenError) as excinfo:
        storage.get_refresh_token()
    assert "auth" in str(excinfo.value).lower()


def test_storage_roundtrip_persists_refresh_token(
    fake_keyring: dict[tuple[str, str], str],
) -> None:
    storage = Storage(client_id="client_abc")
    storage.set_refresh_token("rt_abc")
    assert storage.get_refresh_token() == "rt_abc"
    assert fake_keyring[("spotify-mcp", "client_abc")] == "rt_abc"


def test_storage_clear_is_idempotent(
    fake_keyring: dict[tuple[str, str], str],
) -> None:
    storage = Storage(client_id="client_abc")
    storage.set_refresh_token("rt_abc")
    storage.clear()
    storage.clear()  # second clear must not raise
    with pytest.raises(NoRefreshTokenError):
        storage.get_refresh_token()
