"""MCP server entry point.

Phase F of dev-spotify-mcp-rewrite fills this in. Until then, `run()` exists
only so `spotify_mcp:main` is type-checkable and importable.
"""

from __future__ import annotations


async def run() -> None:
    raise NotImplementedError("server.run() is not implemented yet (Phase F)")
