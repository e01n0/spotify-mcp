# spotify-mcp

An MCP server for Spotify — 23 flat tools, PKCE auth, OS-keychain token storage.

Targets the post-February-2026 Spotify Web API surface. Built with `httpx` + `mcp` + `pydantic` + `keyring`. No `spotipy`, no `client_secret`, no `.cache` files in your CWD.

## Status

🚧 Pre-release. APIs and tool names may change before v1.

## Features

- 23 flat MCP tools (one verb per tool — no action-dispatched mega-tools)
- OAuth 2.0 Authorization Code + PKCE (no client_secret needed)
- Refresh tokens stored in the OS keychain via `keyring`
- Auto-refresh on 401, single retry with `Retry-After` on 429
- Post-Feb-2026 endpoints only (`/me/playlists`, `/playlists/{id}/items`)

## Install

Via `uvx` (recommended):

```bash
uvx --from git+https://github.com/e01n0/spotify-mcp spotify-mcp
```

Local development:

```bash
git clone https://github.com/e01n0/spotify-mcp.git
cd spotify-mcp
uv sync --dev
uv run spotify-mcp
```

## Spotify App Setup

TBD — fill in once auth flow is wired.

## Claude Desktop Config

TBD — fill in once entry point is verified.

## Troubleshooting

TBD.

## Acknowledgments

Inspired by [varunneal/spotify-mcp](https://github.com/varunneal/spotify-mcp). This is a from-scratch rewrite for the post-Feb-2026 API and `uvx`-friendly auth storage.

## License

MIT — see [LICENSE](LICENSE).
