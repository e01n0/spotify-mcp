"""spotify-mcp — MCP server for Spotify with PKCE auth and keyring storage."""

from __future__ import annotations

import asyncio
import os
import sys


def main() -> None:
    """Entry point dispatcher.

    Subcommands:
        (no args)  Run the MCP stdio server (default — for Claude Desktop).
        auth       Run the one-shot PKCE auth flow to populate the OS keychain.
        --help     Print usage and exit.
    """
    argv = sys.argv[1:]

    if argv and argv[0] in {"-h", "--help"}:
        _print_usage()
        return

    if argv and argv[0] == "auth":
        asyncio.run(_run_auth())
        return

    from spotify_mcp.server import run

    asyncio.run(run())


async def _run_auth() -> None:
    from spotify_mcp.auth import DEFAULT_SCOPES, PKCEFlow
    from spotify_mcp.storage import Storage

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    if not client_id:
        print("ERROR: SPOTIFY_CLIENT_ID env var must be set.", file=sys.stderr)
        sys.exit(1)

    port = int(os.environ.get("SPOTIFY_CALLBACK_PORT", "8888"))

    print(
        f"Opening Spotify authorization in your browser. Callback expected on "
        f"http://127.0.0.1:{port}/callback (must match your Spotify app's "
        f"redirect URI)."
    )

    flow = PKCEFlow(client_id, callback_port=port)
    tokens = await flow.run_authorization(DEFAULT_SCOPES)
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print(
            "ERROR: Spotify did not return a refresh_token. "
            "Check that PKCE is enabled for your app.",
            file=sys.stderr,
        )
        sys.exit(2)

    Storage(client_id).set_refresh_token(str(refresh_token))
    print("Refresh token saved to OS keychain. Spotify-mcp is ready to use.")


def _print_usage() -> None:
    print(
        "spotify-mcp — MCP server for Spotify\n"
        "\n"
        "USAGE:\n"
        "    spotify-mcp           Run MCP stdio server (default, for Claude Desktop)\n"
        "    spotify-mcp auth      One-shot PKCE auth flow (run once to populate keychain)\n"
        "    spotify-mcp --help    This message\n"
        "\n"
        "ENVIRONMENT:\n"
        "    SPOTIFY_CLIENT_ID         Required. Your Spotify app client ID.\n"
        "    SPOTIFY_CALLBACK_PORT     Optional. PKCE loopback port (default: 8888).\n"
    )


__all__ = ["main"]
