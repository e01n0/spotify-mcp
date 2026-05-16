---
name: spotify-mood-mix
description: "Use when the user wants to GENERATE a playlist or queue from a vibe, mood, or theme rather than naming specific tracks. Covers: 'make a playlist for late-night drives', 'build a dark americana mix', 'queue something melancholy and acoustic', 'I need workout music', 'put together a wedding ceremony playlist'. Use this skill to brainstorm tracks from music knowledge, search Spotify to verify availability, then either queue them or create a playlist. Requires the spotify-mcp server (mcp__spotify__*)."
allowed-tools:
  - mcp__spotify__*
---

# Spotify Mood Mix Builder

The user is asking for music by VIBE, not by NAME. Your job: turn the vibe into concrete tracks, then deliver via either queue or playlist.

## Critical context

**Spotify's `recommendations`, `related-artists`, and `audio-features` endpoints were REMOVED in February 2026.** You cannot ask the API for similar songs or genre-tagged suggestions. **ALL the curation intelligence comes from YOU** — your music knowledge generating concrete `artist + track` queries that you then search.

## Workflow

### 1. Clarify the vibe (sparingly)
Ask AT MOST one question, only if essential to the output:
- "8-10 tracks or a full hour+ playlist?"
- "Queue tracks to play now, or create a saved playlist?"
- "Should I lean familiar or surprise you with deeper cuts?"

Skip the question if the user's request already implies the answer. Don't interrogate.

### 2. Brainstorm 8-15 candidate tracks
Generate specific `<artist> - <track>` candidates that fit the vibe. Be deliberate:
- **Variety**: don't suggest 5 songs from the same artist unless the user asked for an artist-deep mix
- **Specificity**: "Townes Van Zandt - Pancho and Lefty", not "something by Townes Van Zandt"
- **Vibe coherence**: every track should make sense next to the previous one

### 3. Search and verify
For each candidate:
```
mcp__spotify__search_tracks(query="<artist> <track>", limit=3)
```
Pick the best match (usually the first studio version). Skip candidates with no results — don't paper over gaps.

### 4. Deliver

**Queue path** (when user wants to listen now):
- `mcp__spotify__add_to_queue(uri=<track_uri>)` for each in order.
- Confirm: "Queued 12 tracks. Hit play to start."

**Playlist path** (when user wants to save):
- `mcp__spotify__create_playlist(name=<descriptive>)` — pick a vibey name reflecting the mood ("Late Night Drive", "Murder Ballads & Mercury", "Iron in the Soul").
- `mcp__spotify__add_tracks_to_playlist(playlist_id=..., uris=[...all URIs...])` — one batched call.
- Confirm: "'<playlist_name>' (private) — 12 tracks added."

## Anti-patterns

- **Don't pad to a round number.** 8 strong matches beat 15 mediocre ones. If the vibe is narrow and you only know 6 tracks that genuinely fit, ship 6.
- **Don't suggest songs Spotify might not have.** If you're not sure something's on Spotify (extreme rarities, regional releases), search first before committing it to a playlist message.
- **Don't ignore the `public=False` default.** Playlists you create are private by default and should stay that way unless the user explicitly asks for public.
- **Don't fabricate genre tags or "audio features".** Those endpoints are gone. Your only ground truth is what the user said + your knowledge.

## Style

Lead with the playlist name and a one-line vibe summary, then the track list:

```
**Iron in the Soul** — slow-burning Americana, regret-tinted but not maudlin

1. Townes Van Zandt — Pancho and Lefty
2. Jason Isbell — Cover Me Up
3. ...
```

Don't pre-explain your methodology unless asked.
