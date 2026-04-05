"""Integration tests for admin hotel profile update route."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
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


class _TransactionContext:
    async def __aenter__(self) -> _TransactionContext:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        _ = (exc_type, exc, tb)
        return False


class _FakeConnection:
    def __init__(self) -> None:
        self.hotels: dict[int, dict[str, object]] = {
            21966: {"hotel_id": 21966, "profile_json": "{}"},
        }
        self.facts_versions: list[dict[str, object]] = []
        self.facts_events: list[dict[str, object]] = []
        self.facts_current: dict[int, dict[str, object]] = {}
        self.last_profile_json_raw: str | None = None
        self.last_profile_json_decoded: dict[str, object] | None = None

    def transaction(self) -> _TransactionContext:
        return _TransactionContext()

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
        if "INSERT INTO hotel_facts_versions" in query:
            hotel_id = int(args[0])
            version = int(args[1])
            checksum = str(args[2])
            source_profile_checksum = str(args[3])
            source_profile_json = orjson.loads(str(args[4]))
            facts_json = orjson.loads(str(args[5]))
            validation_json = orjson.loads(str(args[6]))
            published_by = str(args[7])
            published_at = datetime.now(UTC)
            self.facts_versions.append(
                {
                    "hotel_id": hotel_id,
                    "version": version,
                    "checksum": checksum,
                    "source_profile_json": source_profile_json,
                    "facts_json": facts_json,
                    "source_profile_checksum": source_profile_checksum,
                    "validation_json": validation_json,
                    "published_by": published_by,
                    "published_at": published_at,
                    "created_at": published_at,
                }
            )
            return "INSERT 0 1"
        if "INSERT INTO hotel_facts_current" in query:
            hotel_id = int(args[0])
            version = int(args[1])
            checksum = str(args[2])
            self.facts_current[hotel_id] = {
                "hotel_id": hotel_id,
                "version": version,
                "checksum": checksum,
                "published_at": datetime.now(UTC),
            }
            return "INSERT 0 1"
        if "INSERT INTO hotel_facts_events" in query:
            hotel_id = int(args[0])
            version = int(args[1])
            checksum = str(args[2])
            event_type = str(args[3])
            actor = str(args[4])
            metadata_json = orjson.loads(str(args[5]))
            self.facts_events.append(
                {
                    "event_id": len(self.facts_events) + 1,
                    "hotel_id": hotel_id,
                    "event_type": event_type,
                    "version": version,
                    "checksum": checksum,
                    "actor": actor,
                    "metadata_json": metadata_json,
                    "occurred_at": datetime.now(UTC),
                }
            )
            return "INSERT 0 1"
        raise AssertionError(f"Unsupported execute query: {query}")

    async def fetchrow(self, query: str, *args: object) -> dict[str, object] | None:
        if "SELECT * FROM hotels WHERE hotel_id = $1" in query:
            hotel_id = int(args[0])
            row = self.hotels.get(hotel_id)
            if row is None:
                return None
            return dict(row)
        if "FROM hotel_facts_current c" in query and "JOIN hotel_facts_versions v" in query:
            hotel_id = int(args[0])
            pointer = self.facts_current.get(hotel_id)
            if pointer is None:
                return None
            for row in self.facts_versions:
                if int(row["hotel_id"]) == hotel_id and int(row["version"]) == int(pointer["version"]):
                    return {
                        "version": int(row["version"]),
                        "published_by": row["published_by"],
                        "published_at": row["published_at"],
                        "checksum": row["checksum"],
                        "source_profile_checksum": row["source_profile_checksum"],
                        "validation_json": row["validation_json"],
                    }
            return None
        if "FROM hotel_facts_versions v" in query and "WHERE v.hotel_id = $1 AND v.version = $2" in query:
            hotel_id = int(args[0])
            version = int(args[1])
            current = self.facts_current.get(hotel_id)
            for row in self.facts_versions:
                if int(row["hotel_id"]) == hotel_id and int(row["version"]) == version:
                    payload = dict(row)
                    payload["is_current"] = bool(current and int(current["version"]) == version)
                    return payload
            return None
        raise AssertionError(f"Unsupported fetchrow query: {query}")

    async def fetch(self, query: str, *args: object) -> list[dict[str, object]]:
        if "FROM hotel_facts_versions v" in query:
            hotel_id = int(args[0])
            current = self.facts_current.get(hotel_id)
            rows = []
            for row in self.facts_versions:
                if int(row["hotel_id"]) != hotel_id:
                    continue
                payload = dict(row)
                payload["is_current"] = bool(current and int(current["version"]) == int(row["version"]))
                rows.append(payload)
            rows.sort(key=lambda item: int(item["version"]), reverse=True)
            return rows
        if "FROM hotel_facts_events" in query:
            hotel_id = int(args[0])
            rows = [dict(row) for row in self.facts_events if int(row["hotel_id"]) == hotel_id]
            rows.sort(key=lambda item: (item["occurred_at"], item["event_id"]), reverse=True)
            return rows
        raise AssertionError(f"Unsupported fetch query: {query}")

    async def fetchval(self, query: str, *args: object) -> int:
        if "SELECT COALESCE(MAX(version), 0) FROM hotel_facts_versions" in query:
            hotel_id = int(args[0])
            versions = [int(row["version"]) for row in self.facts_versions if int(row["hotel_id"]) == hotel_id]
            return max(versions) if versions else 0
        raise AssertionError(f"Unsupported fetchval query: {query}")


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


async def test_update_hotel_profile_rejects_hotel_id_mismatch(
    admin_hotel_client: tuple[httpx.AsyncClient, _FakeConnection, str],
    sample_profile_payload: dict[str, object],
) -> None:
    client, _, token = admin_hotel_client
    payload = dict(sample_profile_payload)
    payload["hotel_id"] = 12345

    response = await client.put(
        "/api/v1/admin/hotels/21966/profile",
        json={"profile_json": payload},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "eşleşmiyor" in response.json()["detail"]


async def test_update_hotel_profile_returns_conflict_when_checksum_is_stale(
    admin_hotel_client: tuple[httpx.AsyncClient, _FakeConnection, str],
    sample_profile_payload: dict[str, object],
) -> None:
    client, _, token = admin_hotel_client

    response = await client.put(
        "/api/v1/admin/hotels/21966/profile",
        json={
            "profile_json": sample_profile_payload,
            "expected_source_profile_checksum": "f" * 64,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "hotel_profile_conflict"
    assert detail["expected_source_profile_checksum"] == "f" * 64
    assert isinstance(detail["current_source_profile_checksum"], str)


async def test_update_hotel_profile_records_draft_save_event_when_live_version_exists(
    admin_hotel_client: tuple[httpx.AsyncClient, _FakeConnection, str],
    sample_profile_payload: dict[str, object],
) -> None:
    client, connection, token = admin_hotel_client
    connection.hotels[21966]["profile_json"] = orjson.dumps(sample_profile_payload).decode()
    connection.facts_versions.append(
        {
            "hotel_id": 21966,
            "version": 7,
            "checksum": "c" * 64,
            "source_profile_json": {"hotel_id": 21966},
            "facts_json": {"hotel_id": 21966},
            "source_profile_checksum": "b" * 64,
            "validation_json": {"blockers": [], "warnings": []},
            "published_by": "ops_admin",
            "published_at": datetime.now(UTC),
            "created_at": datetime.now(UTC),
        }
    )
    connection.facts_current[21966] = {
        "hotel_id": 21966,
        "version": 7,
        "checksum": "c" * 64,
        "published_at": datetime.now(UTC),
    }

    response = await client.put(
        "/api/v1/admin/hotels/21966/profile",
        json={"profile_json": sample_profile_payload},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    draft_events = [item for item in connection.facts_events if item["event_type"] == "DRAFT_SAVE"]
    assert draft_events
    assert draft_events[0]["version"] == 7
    assert draft_events[0]["actor"] == "ops_admin"
    assert isinstance(draft_events[0]["metadata_json"].get("draft_facts_checksum"), str)
    assert isinstance(draft_events[0]["metadata_json"].get("source_profile_checksum"), str)


async def test_publish_hotel_facts_creates_current_version(
    admin_hotel_client: tuple[httpx.AsyncClient, _FakeConnection, str],
    sample_profile_payload: dict[str, object],
) -> None:
    client, connection, token = admin_hotel_client
    connection.hotels[21966]["profile_json"] = orjson.dumps(sample_profile_payload).decode()

    response = await client.post(
        "/api/v1/admin/hotels/21966/facts/publish",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["published"] is True
    assert payload["version"] == 1
    assert payload["facts_status"]["state"] == "in_sync"
    assert connection.facts_versions
    assert connection.facts_current[21966]["version"] == 1


async def test_get_hotel_facts_versions_and_events_return_published_rows(
    admin_hotel_client: tuple[httpx.AsyncClient, _FakeConnection, str],
) -> None:
    client, connection, token = admin_hotel_client
    connection.facts_versions.append(
        {
            "hotel_id": 21966,
            "version": 3,
            "checksum": "b" * 64,
            "source_profile_json": {"hotel_id": 21966},
            "facts_json": {"hotel_id": 21966},
            "source_profile_checksum": "a" * 64,
            "validation_json": {"blockers": [], "warnings": []},
            "published_by": "ops_admin",
            "published_at": datetime.now(UTC),
            "created_at": datetime.now(UTC),
        }
    )
    connection.facts_current[21966] = {
        "hotel_id": 21966,
        "version": 3,
        "checksum": "b" * 64,
        "published_at": datetime.now(UTC),
    }
    connection.facts_events.append(
        {
            "event_id": 1,
            "hotel_id": 21966,
            "event_type": "PUBLISH",
            "version": 3,
            "checksum": "b" * 64,
            "actor": "ops_admin",
            "metadata_json": {"source_profile_checksum": "a" * 64},
            "occurred_at": datetime.now(UTC),
        }
    )

    versions_response = await client.get(
        "/api/v1/admin/hotels/21966/facts/versions",
        headers={"Authorization": f"Bearer {token}"},
    )
    events_response = await client.get(
        "/api/v1/admin/hotels/21966/facts/events",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert versions_response.status_code == 200
    assert events_response.status_code == 200
    versions_payload = versions_response.json()
    events_payload = events_response.json()
    assert versions_payload["items"][0]["version"] == 3
    assert versions_payload["items"][0]["is_current"] is True
    assert events_payload["items"][0]["event_type"] == "PUBLISH"
