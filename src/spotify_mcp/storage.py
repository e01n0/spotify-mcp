"""Refresh-token persistence via the OS keychain (`keyring`).

No CWD `.cache` files. No plaintext on disk. If the keyring backend is
unavailable the calling tool surfaces a structured error — we never silently
fall back to writing tokens beside the script.
"""

from __future__ import annotations

import contextlib

import keyring
import keyring.errors

SERVICE = "spotify-mcp"


class NoRefreshTokenError(Exception):
    """No refresh token stored for the given client_id — caller must re-auth."""


class Storage:
    """Thin wrapper over `keyring`, keyed by Spotify `client_id`."""

    def __init__(self, client_id: str) -> None:
        self._client_id = client_id

    def get_refresh_token(self) -> str:
        token = keyring.get_password(SERVICE, self._client_id)
        if not token:
            raise NoRefreshTokenError(
                f"No refresh token stored for client_id={self._client_id!r}. "
                "Run the auth flow to obtain one."
            )
        return token

    def set_refresh_token(self, token: str) -> None:
        keyring.set_password(SERVICE, self._client_id, token)

    def clear(self) -> None:
        # Already-absent is the desired end state — idempotent, not silent failure.
        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(SERVICE, self._client_id)
