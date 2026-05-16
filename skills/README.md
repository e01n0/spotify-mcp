# spotify-mcp skills

Workflow skills that drive the spotify-mcp server. Drop these into Claude's skills directory and Claude will know when to invoke them.

## What's here

| Skill                  | When it triggers                                                                  |
|------------------------|-----------------------------------------------------------------------------------|
| `spotify-playback`     | Playback control — play X, pause, skip, queue, volume, seek, "what's playing"     |
| `spotify-playlist`     | Playlist CRUD — create, list, add/remove tracks, rename, view metadata            |
| `spotify-mood-mix`     | Vibe-driven generation — "build me a playlist for X", "queue something Y"         |

## Install

Skills live in `~/.claude/skills/` on macOS and Linux (Claude Code and Claude Desktop share this location for user skills).

```bash
# From the spotify-mcp repo root
cp -r skills/spotify-playback skills/spotify-playlist skills/spotify-mood-mix ~/.claude/skills/
```

Or symlink so updates from the repo propagate automatically:

```bash
for s in spotify-playback spotify-playlist spotify-mood-mix; do
  ln -snf "$(pwd)/skills/$s" "$HOME/.claude/skills/$s"
done
```

## Prerequisites

These skills assume the `spotify-mcp` server is wired into your Claude config and authenticated. See the [main README](../README.md) for setup. The skills reference tools as `mcp__spotify__*` — that prefix maps to whatever key you used in `claude_desktop_config.json` (the canonical key is `spotify`).

## Personalizing

The skills are intentionally generic. To add personal taste-anchors (e.g. "I have a playlist called X and these are its touchstone artists Y"), copy a skill into `~/.claude/skills/` under a new name, edit the `description` and body, and Claude will pick it up alongside the generic ones.

## Style guide

All three skills are written with the same constraints in mind:

- **Confirm in one line.** No multi-paragraph summaries of what just happened.
- **Surface errors verbatim.** When the MCP returns `error: no_refresh_token`, repeat the remediation — don't paper over it.
- **Respect the private-by-default playlist convention.** The server defaults `public=False`. Skills should too.
