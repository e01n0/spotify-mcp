---
name: spotify-playback
description: "Use when the user wants to CONTROL Spotify playback: play a track/album/playlist by name, pause, resume, skip, go back, queue something, change volume, seek to a position, or check what's playing and on which device. Covers natural-language requests like 'play Pancho and Lefty by Townes Van Zandt', 'pause', 'skip this', 'queue up the next Halsey album', 'what's playing right now?', 'crank the volume to 80'. Requires the spotify-mcp server (mcp__spotify__*) to be configured."
allowed-tools:
  - mcp__spotify__*
---

# Spotify Playback Control

The spotify-mcp server exposes 23 flat tools for the Spotify Web API. This skill covers everything related to controlling and inspecting playback.

## Common requests

### "Play X" / "Put on X"
1. Identify what X is — a track, an album, an artist, a playlist? Ambiguity matters because the URI type drives a different request shape (the server handles it, but you need to search the right thing).
2. Search with the right type:
   - Single song → `mcp__spotify__search_tracks`
   - Full LP → `mcp__spotify__search_albums`
   - Artist context ("play Townes Van Zandt") → `mcp__spotify__search_artists`
   - Playlist → `mcp__spotify__search_playlists`
3. Pick the best match. Prefer the studio version over live recordings unless the user said "live".
4. `mcp__spotify__start_playback(uri=<chosen_uri>)`. The server detects the URI type:
   - `spotify:track:...` → goes in `uris` field (single-track playback)
   - `spotify:album|playlist|artist:...` → goes in `context_uri` (context playback)

### "Pause" / "Resume" / "Skip" / "Previous"
- `mcp__spotify__pause_playback`
- `mcp__spotify__start_playback` with no `uri` resumes the current context
- `mcp__spotify__next_track` / `mcp__spotify__previous_track`

### "What's playing?"
- `mcp__spotify__get_current_playback` — returns `{is_playing, progress_ms, track}`.
- If `is_playing: false`, just say so plainly. Don't invent context.

### "Queue X"
- Search for X, then `mcp__spotify__add_to_queue(uri=<track_uri>)`.

### "What devices are available?" / "Play on the kitchen speaker"
- `mcp__spotify__list_devices` returns DTOs with `id`, `name`, `type`, `is_active`, `volume_percent`.
- If the user names a device, find its `id` and pass `device_id=...` to subsequent playback calls.

### Volume / Seek
- `mcp__spotify__set_volume(volume_percent=0..100)`
- `mcp__spotify__seek(position_ms=...)`

## Failure modes you'll see

- **No active device** — `list_devices` returns `[]` or no device has `is_active=true`. Tell the user: "No active Spotify Connect device — open Spotify somewhere first." Don't attempt `start_playback`; it'll 404.
- **`{"error": "no_refresh_token"}`** — the user hasn't run the auth flow. Surface the remediation verbatim: "Run `spotify-mcp auth` once locally to populate the OS keychain."
- **`{"error": "rate_limited"}`** — Spotify rate-limited even after honoring `Retry-After` once. Wait 10-20s and try again, or move on.
- **`{"error": "auth"}`** — refresh token revoked or invalidated server-side. User needs to re-run `spotify-mcp auth`.

## Style

Confirm what you did in ONE line. "Playing 'Pancho and Lefty' by Townes Van Zandt." That's enough. Don't pre-explain your tool choices or paste the full DTO back at the user.
