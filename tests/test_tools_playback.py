"""Phase E TDD tests 12-14: playback URI routing + no-device graceful handling."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from spotify_mcp.auth import PKCEFlow
from spotify_mcp.client import SpotifyClient
from spotify_mcp.models import ListDevicesInput, StartPlaybackInput
from spotify_mcp.storage import Storage
from spotify_mcp.tools import list_devices, start_playback


@pytest.fixture
async def client(
    fake_keyring: dict[tuple[str, str], str],
) -> AsyncIterator[SpotifyClient]:
    storage = Storage(client_id="CID")
    storage.set_refresh_token("rt_initial")
    sc = SpotifyClient(client_id="CID", storage=storage, auth=PKCEFlow("CID"))
    sc._access_token = "at_xyz"
    yield sc
    await sc.aclose()


@respx.mock
async def test_start_playback_with_track_uri_sends_uris_field(client: SpotifyClient) -> None:
    route = respx.put("https://api.spotify.com/v1/me/player/play").mock(
        return_value=httpx.Response(204),
    )

    await start_playback(client, StartPlaybackInput(uri="spotify:track:T"))

    body = json.loads(route.calls.last.request.content)
    assert body == {"uris": ["spotify:track:T"]}


@respx.mock
async def test_start_playback_with_album_uri_sends_context_uri_field(
    client: SpotifyClient,
) -> None:
    route = respx.put("https://api.spotify.com/v1/me/player/play").mock(
        return_value=httpx.Response(204),
    )

    await start_playback(client, StartPlaybackInput(uri="spotify:album:A"))

    body = json.loads(route.calls.last.request.content)
    assert body == {"context_uri": "spotify:album:A"}


@respx.mock
async def test_start_playback_with_playlist_uri_sends_context_uri_field(
    client: SpotifyClient,
) -> None:
    route = respx.put("https://api.spotify.com/v1/me/player/play").mock(
        return_value=httpx.Response(204),
    )

    await start_playback(client, StartPlaybackInput(uri="spotify:playlist:PL"))

    body = json.loads(route.calls.last.request.content)
    assert body == {"context_uri": "spotify:playlist:PL"}


@respx.mock
async def test_list_devices_surfaces_no_active_device_state(client: SpotifyClient) -> None:
    """Empty devices array returns [] cleanly — LLM decides what to do."""
    respx.get("https://api.spotify.com/v1/me/player/devices").mock(
        return_value=httpx.Response(200, json={"devices": []}),
    )

    result = await list_devices(client, ListDevicesInput())
    items = json.loads(result[0].text)
    assert items == []
