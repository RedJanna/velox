from __future__ import annotations

import pytest

from velox.core import burst_buffer


class _FakePipeline:
    def __init__(self, redis: _FakeRedis) -> None:
        self._redis = redis
        self._commands: list[tuple[str, tuple[object, ...]]] = []

    def lrange(self, key: str, start: int, end: int) -> None:
        self._commands.append(("lrange", (key, start, end)))

    def delete(self, key: str) -> None:
        self._commands.append(("delete", (key,)))

    async def execute(self) -> list[object]:
        results: list[object] = []
        for command, args in self._commands:
            if command == "lrange":
                key, start, end = args
                rows = list(self._redis.lists.get(str(key), []))
                if end == -1:
                    end = len(rows) - 1
                results.append(rows[int(start): int(end) + 1])
                continue
            if command == "delete":
                (key,) = args
                await self._redis.delete(str(key))
                results.append(1)
                continue
            raise AssertionError(f"Unsupported pipeline command: {command}")
        return results


class _FakeRedis:
    def __init__(self) -> None:
        self.lists: dict[str, list[bytes]] = {}
        self.values: dict[str, str] = {}

    def pipeline(self, transaction: bool = True) -> _FakePipeline:
        _ = transaction
        return _FakePipeline(self)

    async def rpush(self, key: str, value: bytes) -> int:
        bucket = self.lists.setdefault(key, [])
        bucket.append(value)
        return len(bucket)

    async def expire(self, key: str, seconds: int) -> bool:
        _ = (key, seconds)
        return True

    async def pexpire(self, key: str, milliseconds: int) -> bool:
        _ = milliseconds
        return key in self.values

    async def llen(self, key: str) -> int:
        return len(self.lists.get(key, []))

    async def exists(self, key: str) -> int:
        return 1 if key in self.values else 0

    async def set(
        self,
        key: str,
        value: str,
        *,
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
    ) -> bool:
        _ = (ex, px)
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def delete(self, key: str) -> int:
        removed = 0
        if key in self.values:
            self.values.pop(key, None)
            removed += 1
        if key in self.lists:
            self.lists.pop(key, None)
            removed += 1
        return removed


@pytest.mark.asyncio
async def test_flush_rearms_debounce_when_lock_not_acquired(monkeypatch: pytest.MonkeyPatch) -> None:
    redis = _FakeRedis()
    hotel_id = 21966
    phone_hash = "hash123"
    buf_key = burst_buffer._buf_key(hotel_id, phone_hash)
    tmr_key = burst_buffer._tmr_key(hotel_id, phone_hash)
    buffered = burst_buffer.BufferedMessage(
        message_id="m1",
        phone="905551112233",
        display_name="Guest",
        text="Merhaba",
        timestamp=1,
        message_type="text",
    )
    redis.lists[buf_key] = [burst_buffer._serialize(buffered)]
    redis.values[tmr_key] = "1"

    class _FailingLock:
        async def acquire(self, retries: int = 3, retry_delay: float = 1.0) -> bool:
            _ = (retries, retry_delay)
            return False

        async def release(self) -> None:
            return None

    created_tasks: list[object] = []

    def _capture_task(coro: object) -> object:
        created_tasks.append(coro)
        close = getattr(coro, "close", None)
        if callable(close):
            close()
        return object()

    monkeypatch.setattr(burst_buffer, "ConversationLock", lambda *_args, **_kwargs: _FailingLock())
    monkeypatch.setattr(burst_buffer.asyncio, "create_task", _capture_task)

    callback_calls = 0

    async def _callback(_aggregated: burst_buffer.AggregatedMessage, _hotel_id: int) -> None:
        nonlocal callback_calls
        callback_calls += 1

    await burst_buffer._flush_and_process(redis, hotel_id, phone_hash, _callback)

    assert callback_calls == 0
    assert len(redis.lists.get(buf_key, [])) == 1
    assert redis.values.get(tmr_key) == "1"
    assert created_tasks, "Debounce watcher must be re-armed after lock acquisition failure."
