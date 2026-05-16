---
name: spotify-playlist
description: "Use when the user wants to MANAGE their Spotify playlists: create a new one, list theirs, view one's metadata, rename, change description or visibility, add tracks, or remove tracks. Covers requests like 'add this song to my Outlaw Country Gothic playlist', 'create a new playlist called Late Night Drives', 'show me my playlists', 'rename X to Y', 'remove the last 5 tracks from Z'. Requires the spotify-mcp server (mcp__spotify__*)."
allowed-tools:
  - mcp__spotify__*
---

# Spotify Playlist Curation

You're modifying persistent, user-visible state. Confirm intent before destructive operations.

## Common requests

### "Add track X to playlist Y"
1. `mcp__spotify__list_my_playlists(limit=50)` — find Y by name (case-insensitive). If multiple matches, ASK which one.
2. `mcp__spotify__search_tracks(query=X, limit=3)` — pick the best match.
3. `mcp__spotify__add_tracks_to_playlist(playlist_id=Y.id, uris=[X.uri])`.
4. Confirm: "Added '<track>' to <playlist> (snapshot <snapshot_id>)."

### "Create a playlist called X"
1. `mcp__spotify__create_playlist(name=X)`.
2. **Important default**: `public=False` (private). If the user wants it public, pass `public=True` explicitly. This default deliberately diverges from Spotify's API (which defaults to public) — an AI tool shouldn't accidentally publish to a user's profile.
3. Confirm: "Created '<name>' (private). URI: <uri>."

### "Show my playlists"
- `mcp__spotify__list_my_playlists(limit=50)`. Render as a clean list:
  ```
  - <name> (<total_tracks> tracks, <public|private>)
  ```
- The `limit` caps at 50. If the user clearly has more, raise the limit (max 50 per call) and note the cap.

### "What's in playlist Y?"
- `mcp__spotify__get_playlist(playlist_id=...)` — returns name, description, total_tracks, owner. Track list contents are NOT in the DTO. To see actual tracks, you'd need to play it (`start_playback` with the playlist URI) or extend the tool — flag this limitation rather than fabricate.

### "Remove track X from playlist Y"
1. Find Y's id via `list_my_playlists`.
2. Search for X's URI via `search_tracks`.
3. `mcp__spotify__remove_tracks_from_playlist(playlist_id=Y.id, uris=[X.uri])`.
4. **Caveat**: this removes ALL occurrences of that URI. If the user wants to remove ONE specific position-based occurrence (e.g., "the second time I added it"), the current tool doesn't support that — say so plainly.

### "Rename / update playlist Y"
- `mcp__spotify__change_playlist_details(playlist_id, name=..., description=..., public=...)` — pass ONLY the fields that change.

## Failure modes

- **Playlist not found** in `list_my_playlists` — limit=50 by default; if their library is larger, paginate or note the cap.
- **`error: no_refresh_token`** — user needs to run `spotify-mcp auth`.

## Style

When you add or remove tracks, name BOTH the track AND the playlist AND the new count in one line:
> "Added 'Pancho and Lefty' to Outlaw Country Gothic (now 12 tracks)."

Don't paste the snapshot_id at the user unless they asked for it.
