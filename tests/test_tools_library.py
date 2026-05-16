"""Tests for save_tracks_to_library — uses /me/tracks endpoint, batches of 50 max."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
import pytest
import respx
from pydantic import ValidationError

from spotify_mcp.auth import PKCEFlow
from spotify_mcp.client import SpotifyClient
from spotify_mcp.models import SaveTracksToLibraryInput
from spotify_mcp.storage import Storage
from spotify_mcp.tools import save_tracks_to_library


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
async def test_save_tracks_to_library_uses_me_library_with_uri_param(
    client: SpotifyClient,
) -> None:
    """Feb-2026: PUT /me/library?uris=spotify:track:id1,spotify:track:id2,...

    The legacy /me/tracks PUT now returns 403; library writes consolidated to
    /me/library. Format requires URI-prefixed values in `uris` query (not `ids`).
    """
    route = respx.put("https://api.spotify.com/v1/me/library").mock(
        return_value=httpx.Response(200),
    )

    await save_tracks_to_library(
        client,
        SaveTracksToLibraryInput(track_ids=["track_one", "track_two", "track_three"]),
    )

    call = route.calls.last
    assert call.request.url.path == "/v1/me/library"
    # URIs go in the `uris` query param, comma-separated, with spotify:track: prefix
    url = str(call.request.url)
    assert "uris=" in url
    assert "spotify%3Atrack%3Atrack_one" in url
    assert "spotify%3Atrack%3Atrack_two" in url
    assert "spotify%3Atrack%3Atrack_three" in url


@respx.mock
async def test_save_tracks_to_library_reports_count(client: SpotifyClient) -> None:
    respx.put("https://api.spotify.com/v1/me/library").mock(
        return_value=httpx.Response(200),
    )

    result = await save_tracks_to_library(
        client,
        SaveTracksToLibraryInput(track_ids=["t1", "t2"]),
    )
    payload = json.loads(result[0].text)
    assert payload["saved"] == 2


def test_save_tracks_to_library_rejects_over_50() -> None:
    # Pydantic schema enforces the 50-id cap at validation time
    with pytest.raises(ValidationError):
        SaveTracksToLibraryInput(track_ids=[f"id_{i}" for i in range(51)])


@respx.mock
async def test_client_save_tracks_raises_on_oversize_batch(client: SpotifyClient) -> None:
    # Defense-in-depth: the client method also enforces the cap
    with pytest.raises(ValueError, match="max 50"):
        await client.save_tracks_to_library([f"id_{i}" for i in range(51)])
