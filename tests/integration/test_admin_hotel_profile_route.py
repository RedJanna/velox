"""Integration tests for admin hotel profile update route."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import orjson
import pytest
import yaml
from fastapi import FastAPI

from velox.api.middleware.auth import TokenData, create_access_token
from velox.api.routes import admin
from velox.config.constants import Role
from velox.config.settings import settings


class _AcquireContext:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    async def __aenter__(self) -> _FakeConnection:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        _ = (exc_type, exc, tb)
        return False


class _FakeConnection:
    def __init__(self) -> None:
        self.hotels: dict[int, dict[str, object]] = {
            21966: {"hotel_id": 21966, "profile_json": "{}"},
        }
        self.last_profile_json_raw: str | None = None
        self.last_profile_json_decoded: dict[str, object] | None = None

    async def execute(self, query: str, *args: object) -> str:
        if "UPDATE hotels" in query and "SET profile_json = $1" in query:
            profile_json_raw = args[0]
            hotel_id = int(args[1])
            assert isinstance(profile_json_raw, str)
            decoded = orjson.loads(profile_json_raw)
            assert isinstance(decoded, dict)

            row = self.hotels.get(hotel_id)
            if row is None:
                return "UPDATE 0"

            row["profile_json"] = profile_json_raw
            self.last_profile_json_raw = profile_json_raw
            self.last_profile_json_decoded = decoded
            return "UPDATE 1"
        raise AssertionError(f"Unsupported execute query: {query}")

    async def fetchrow(self, query: str, *args: object) -> dict[str, object] | None:
        if "SELECT * FROM hotels WHERE hotel_id = $1" in query:
            hotel_id = int(args[0])
            row = self.hotels.get(hotel_id)
            if row is None:
                return None
            return dict(row)
        raise AssertionError(f"Unsupported fetchrow query: {query}")


class _FakePool:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def acquire(self) -> _AcquireContext:
        return _AcquireContext(self._connection)


@pytest.fixture
def sample_profile_payload() -> dict[str, object]:
    path = Path("data/hotel_profiles/kassandra_oludeniz.yaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


@pytest.fixture
async def admin_hotel_client(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[tuple[httpx.AsyncClient, _FakeConnection, str]]:
    connection = _FakeConnection()
    app = FastAPI()
    app.state.db_pool = _FakePool(connection)
    app.include_router(admin.router, prefix="/api/v1")

    monkeypatch.setattr(settings, "admin_jwt_secret", "test-secret")
    monkeypatch.setattr(
        admin,
        "save_profile_definition",
        lambda _: Path("data/hotel_profiles/test_profile.yaml"),
    )
    monkeypatch.setattr(admin, "reload_profiles", lambda: None)

    token = create_access_token(
        TokenData(
            user_id=1,
            hotel_id=21966,
            username="ops_admin",
            role=Role.ADMIN,
            display_name="Ops Admin",
        )
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver.local") as client:
        yield client, connection, token


async def test_update_hotel_profile_serializes_profile_json_before_db_write(
    admin_hotel_client: tuple[httpx.AsyncClient, _FakeConnection, str],
    sample_profile_payload: dict[str, object],
) -> None:
    client, connection, token = admin_hotel_client

    response = await client.put(
        "/api/v1/admin/hotels/21966/profile",
        json={"profile_json": sample_profile_payload},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert connection.last_profile_json_raw is not None
    assert connection.last_profile_json_decoded is not None
    assert connection.last_profile_json_decoded["hotel_id"] == sample_profile_payload["hotel_id"]


async def test_update_hotel_profile_returns_404_when_hotel_missing(
    admin_hotel_client: tuple[httpx.AsyncClient, _FakeConnection, str],
    sample_profile_payload: dict[str, object],
) -> None:
    client, _, token = admin_hotel_client

    response = await client.put(
        "/api/v1/admin/hotels/99999/profile",
        json={"profile_json": sample_profile_payload},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Hotel not found"


async def test_get_hotel_decodes_profile_json_string(
    admin_hotel_client: tuple[httpx.AsyncClient, _FakeConnection, str],
) -> None:
    client, connection, token = admin_hotel_client
    connection.hotels[21966]["profile_json"] = orjson.dumps({"hotel_id": 21966, "location": {"city": "Mugla"}}).decode()

    response = await client.get(
        "/api/v1/admin/hotels/21966",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["profile_json"], dict)
    assert payload["profile_json"]["location"]["city"] == "Mugla"


async def test_update_hotel_profile_updates_db_even_if_yaml_write_fails(
    admin_hotel_client: tuple[httpx.AsyncClient, _FakeConnection, str],
    sample_profile_payload: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, connection, token = admin_hotel_client
    cache_calls: list[dict[str, object]] = []

    def _raise_yaml_error(_payload: dict[str, object]) -> Path:
        raise OSError("disk read-only")

    def _cache(payload: dict[str, object]) -> None:
        cache_calls.append(payload)

    monkeypatch.setattr(admin, "save_profile_definition", _raise_yaml_error)
    monkeypatch.setattr(admin, "cache_profile_definition", _cache)

    response = await client.put(
        "/api/v1/admin/hotels/21966/profile",
        json={"profile_json": sample_profile_payload},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert connection.last_profile_json_decoded is not None
    assert connection.last_profile_json_decoded["hotel_id"] == sample_profile_payload["hotel_id"]
    assert cache_calls
