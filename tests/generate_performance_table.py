#!/usr/bin/env python
"""Генерация таблицы производительности для docs/PERFORMANCE_TABLE.md"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
import database


async def benchmark(load: int) -> list[dict]:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    config.DB_URL = path
    await database.init_db()
    await database.create_user(1, "u", "User")
    await database.create_user(2, "h", "Helper", "helper")

    rows = []

    tracemalloc.start()
    t0 = time.perf_counter()
    for i in range(load):
        tid = await database.create_ticket(1, f"Issue {i}")
        if i % 2 == 0:
            await database.accept_ticket(tid, 2)
            await database.close_ticket(tid)
            await database.rate_ticket(tid, (i % 5) + 1)
    seed_ms = (time.perf_counter() - t0) * 1000
    _, peak_seed = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rows.append(
        {
            "load": load,
            "operation": "Создание тикетов (batch)",
            "time_ms": round(seed_ms, 2),
            "memory_kb": round(peak_seed / 1024, 2),
        }
    )

    tracemalloc.start()
    t0 = time.perf_counter()
    await database.get_db_stats()
    stats_ms = (time.perf_counter() - t0) * 1000
    _, peak_stats = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rows.append(
        {
            "load": load,
            "operation": "get_db_stats()",
            "time_ms": round(stats_ms, 2),
            "memory_kb": round(peak_stats / 1024, 2),
        }
    )

    tracemalloc.start()
    t0 = time.perf_counter()
    await database.get_waiting_tickets()
    wait_ms = (time.perf_counter() - t0) * 1000
    _, peak_wait = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rows.append(
        {
            "load": load,
            "operation": "get_waiting_tickets()",
            "time_ms": round(wait_ms, 2),
            "memory_kb": round(peak_wait / 1024, 2),
        }
    )

    from fastapi.testclient import TestClient
    from web.main import app

    client = TestClient(app)
    times = []
    for _ in range(10):
        t0 = time.perf_counter()
        client.get("/api/stats")
        times.append((time.perf_counter() - t0) * 1000)
    rows.append(
        {
            "load": load,
            "operation": "GET /api/stats (среднее, 10 запросов)",
            "time_ms": round(sum(times) / len(times), 2),
            "memory_kb": "—",
        }
    )

    os.unlink(path)
    return rows


def render_markdown(all_rows: list[dict]) -> str:
    lines = [
        "# Таблица производительности — IT Top Support Bot",
        "",
        "Измерения выполняются скриптом `tests/generate_performance_table.py` на локальной SQLite.",
        "",
        "| Нагрузка (тикетов) | Операция | Время (мс) | Память (КБ) |",
        "|-------------------:|----------|-----------:|------------:|",
    ]
    for r in all_rows:
        lines.append(
            f"| {r['load']} | {r['operation']} | {r['time_ms']} | {r['memory_kb']} |"
        )
    lines.extend(
        [
            "",
            "## Условия",
            "",
            "- ОС: Windows, Python 3.11+",
            "- БД: временный файл SQLite (изолированный прогон)",
            "- Память: `tracemalloc` peak на время операции",
            "",
            "## Перегенерация",
            "",
            "```bat",
            "venv\\Scripts\\python.exe tests\\generate_performance_table.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


async def main():
    loads = (10, 100, 500)
    all_rows: list[dict] = []
    for load in loads:
        print(f"Benchmark load={load}...")
        all_rows.extend(await benchmark(load))

    out = PROJECT_ROOT / "docs" / "PERFORMANCE_TABLE.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(render_markdown(all_rows), encoding="utf-8")
    print(f"Saved: {out}")


if __name__ == "__main__":
    asyncio.run(main())
