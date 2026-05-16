"""Shared test fixtures: fake keyring, sample-response loader, http transport."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import keyring
import keyring.errors
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fake_keyring(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[tuple[str, str], str]]:
    """In-memory keyring backend keyed by (service, username)."""
    store: dict[tuple[str, str], str] = {}

    def get_password(service: str, username: str) -> str | None:
        return store.get((service, username))

    def set_password(service: str, username: str, password: str) -> None:
        store[(service, username)] = password

    def delete_password(service: str, username: str) -> None:
        if (service, username) not in store:
            raise keyring.errors.PasswordDeleteError("not found")
        del store[(service, username)]

    monkeypatch.setattr(keyring, "get_password", get_password)
    monkeypatch.setattr(keyring, "set_password", set_password)
    monkeypatch.setattr(keyring, "delete_password", delete_password)
    yield store


def load_fixture(name: str) -> dict[str, Any]:
    """Load a JSON fixture from tests/fixtures/."""
    return json.loads((FIXTURES / name).read_text())
