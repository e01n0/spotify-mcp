"""spotify-mcp — MCP server for Spotify with PKCE auth and keyring storage."""

from __future__ import annotations

import asyncio


def main() -> None:
    from spotify_mcp.server import run

    asyncio.run(run())


__all__ = ["main"]
