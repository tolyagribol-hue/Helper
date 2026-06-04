"""
Нагрузочные тесты: скорость и память при разных объёмах данных.
Результаты сохраняются в docs/PERFORMANCE_TABLE.md
"""
from __future__ import annotations

import asyncio
import time
import tracemalloc
from pathlib import Path

import pytest

import database

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOAD_LEVELS = (10, 100, 500)


async def _seed_tickets(count: int) -> None:
    await database.create_user(1, "load_user", "Load")
    await database.create_user(2, "load_helper", "Helper", "helper")
    for i in range(count):
        tid = await database.create_ticket(1, f"Load test issue #{i}")
        if i % 2 == 0:
            await database.accept_ticket(tid, 2)
            await database.close_ticket(tid)
            await database.rate_ticket(tid, (i % 5) + 1)


@pytest.mark.parametrize("load", LOAD_LEVELS)
class TestPerformance:
    async def test_create_and_stats_speed(self, test_db, load: int):
        tracemalloc.start()
        t0 = time.perf_counter()
        await _seed_tickets(load)
        stats = await database.get_db_stats()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert stats["total_tickets"] == load
        assert elapsed_ms < max(5000, load * 50), f"Too slow at load={load}: {elapsed_ms:.1f}ms"

    async def test_waiting_tickets_query(self, test_db, load: int):
        await _seed_tickets(load)
        tracemalloc.start()
        t0 = time.perf_counter()
        waiting = await database.get_waiting_tickets()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert isinstance(waiting, list)


class TestApiPerformance:
    def test_api_stats_response_time(self, test_db_sync):
        from fastapi.testclient import TestClient
        from web.main import app

        client = TestClient(app)
        times = []
        for _ in range(20):
            t0 = time.perf_counter()
            r = client.get("/api/stats")
            times.append((time.perf_counter() - t0) * 1000)
            assert r.status_code == 200
        avg = sum(times) / len(times)
        assert avg < 500, f"API too slow: {avg:.1f}ms avg"
