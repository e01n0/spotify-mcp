"""OAuth 2.0 Authorization Code + PKCE for Spotify.

Public clients (this MCP server is one) must not ship a `client_secret` —
PKCE per RFC 7636 is the IETF-recommended substitute. Callback is captured
on a loopback HTTP server bound to 127.0.0.1 (never 0.0.0.0).
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import secrets
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

import httpx

AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
DEFAULT_TIMEOUT_S = 120.0


class AuthorizationError(Exception):
    """PKCE authorization flow failed (timeout, user denial, network error)."""


class PKCEFlow:
    """PKCE flow handler. Static helpers usable without instantiation."""

    def __init__(self, client_id: str, *, callback_port: int = 8888) -> None:
        self._client_id = client_id
        self._port = callback_port

    @staticmethod
    def generate_verifier() -> str:
        """RFC 7636 §4.1: high-entropy code_verifier, 43-128 unreserved chars.

        `secrets.token_urlsafe(32)` yields a 43-char base64url string drawn
        from `[A-Za-z0-9\\-_]`, a subset of the RFC 7636 unreserved set.
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def challenge_for(verifier: str) -> str:
        """RFC 7636 §4.2: code_challenge = base64url(sha256(verifier)), no padding."""
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    @property
    def redirect_uri(self) -> str:
        # Spotify requires 127.0.0.1 (not `localhost`) for loopback redirects.
        return f"http://127.0.0.1:{self._port}/callback"

    def build_authorize_url(self, scopes: list[str], verifier: str) -> str:
        params = {
            "client_id": self._client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "code_challenge_method": "S256",
            "code_challenge": self.challenge_for(verifier),
        }
        return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    async def run_authorization(
        self,
        scopes: list[str],
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> dict[str, Any]:
        """Open browser, capture the OAuth `code`, exchange for tokens."""
        verifier = self.generate_verifier()
        auth_url = self.build_authorize_url(scopes, verifier)

        code = await asyncio.to_thread(self._capture_code_via_loopback, auth_url, timeout_s)

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self._client_id,
                    "code_verifier": verifier,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Exchange a refresh_token for a fresh access_token (and possibly a new RT)."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self._client_id,
                },
            )
            resp.raise_for_status()
            return resp.json()

    def _capture_code_via_loopback(self, auth_url: str, timeout_s: float) -> str:
        captured: dict[str, str] = {}

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                qs = urllib.parse.parse_qs(parsed.query)
                if "code" in qs:
                    captured["code"] = qs["code"][0]
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"Authorization complete. You can close this tab.")
                elif "error" in qs:
                    captured["error"] = qs["error"][0]
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Authorization failed.")
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format: str, *args: Any) -> None:
                # Suppress default stderr noise from BaseHTTPRequestHandler.
                return

        server = HTTPServer(("127.0.0.1", self._port), _Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            webbrowser.open(auth_url)
            deadline = time.monotonic() + timeout_s
            while time.monotonic() < deadline:
                if "code" in captured:
                    return captured["code"]
                if "error" in captured:
                    raise AuthorizationError(f"Spotify returned error: {captured['error']}")
                time.sleep(0.1)
            raise AuthorizationError(f"Timed out after {timeout_s}s waiting for OAuth callback.")
        finally:
            server.shutdown()
            server.server_close()
