"""Tests for SpotifyClient — bearer attach, refresh-on-401, Retry-After on 429."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from spotify_mcp.auth import PKCEFlow
from spotify_mcp.client import AuthenticationError, RateLimitError, SpotifyClient
from spotify_mcp.storage import Storage


@pytest.fixture
async def client(
    fake_keyring: dict[tuple[str, str], str],
) -> AsyncIterator[SpotifyClient]:
    storage = Storage(client_id="CID")
    storage.set_refresh_token("rt_initial")
    sc = SpotifyClient(client_id="CID", storage=storage, auth=PKCEFlow("CID"))
    sc._access_token = "at_xyz"  # prime to skip first-call refresh in tests that don't care
    yield sc
    await sc.aclose()


@respx.mock
async def test_client_attaches_bearer_token(client: SpotifyClient) -> None:
    route = respx.get("https://api.spotify.com/v1/me").mock(
        return_value=httpx.Response(200, json={"id": "u"}),
    )
    await client._request("GET", "/me")
    assert route.calls.last.request.headers["Authorization"] == "Bearer at_xyz"


@respx.mock
async def test_client_refreshes_on_401_then_retries_once(
    client: SpotifyClient,
    fake_keyring: dict[tuple[str, str], str],
) -> None:
    api_route = respx.get("https://api.spotify.com/v1/me").mock(
        side_effect=[
            httpx.Response(401, json={"error": "expired"}),
            httpx.Response(200, json={"id": "u"}),
        ],
    )
    token_route = respx.post("https://accounts.spotify.com/api/token").mock(
        return_value=httpx.Response(
            200,
            json={"access_token": "at_new", "refresh_token": "rt_new", "expires_in": 3600},
        ),
    )

    result = await client._request("GET", "/me")

    assert result == {"id": "u"}
    assert token_route.call_count == 1
    assert api_route.call_count == 2
    assert client._access_token == "at_new"
    # Token rotation must persist — silently dropping the rotated RT invalidates the stored one.
    assert fake_keyring[("spotify-mcp", "CID")] == "rt_new"


@respx.mock
async def test_client_raises_after_second_401(client: SpotifyClient) -> None:
    respx.get("https://api.spotify.com/v1/me").mock(
        return_value=httpx.Response(401, json={"error": "bad_token"}),
    )
    respx.post("https://accounts.spotify.com/api/token").mock(
        return_value=httpx.Response(200, json={"access_token": "at_new", "expires_in": 3600}),
    )

    with pytest.raises(AuthenticationError):
        await client._request("GET", "/me")


@respx.mock
async def test_client_honors_retry_after_on_429(
    client: SpotifyClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("spotify_mcp.client.asyncio.sleep", fake_sleep)

    respx.get("https://api.spotify.com/v1/me").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"ok": True}),
        ],
    )

    result = await client._request("GET", "/me")
    assert result == {"ok": True}
    assert sleeps == [0.0]


@respx.mock
async def test_client_raises_after_second_429(
    client: SpotifyClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_sleep(seconds: float) -> None:
        return

    monkeypatch.setattr("spotify_mcp.client.asyncio.sleep", fake_sleep)

    respx.get("https://api.spotify.com/v1/me").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"}),
    )

    with pytest.raises(RateLimitError):
        await client._request("GET", "/me")
