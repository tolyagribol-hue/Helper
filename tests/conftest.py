"""Shared fixtures: temp DB, project root on sys.path."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
async def test_db(monkeypatch):
    """Isolated SQLite file; patches config.DB_URL for the test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    import config
    import database

    monkeypatch.setattr(config, "DB_URL", path)
    await database.init_db()
    yield path

@pytest.fixture
def test_db_sync(monkeypatch):
    """Sync wrapper for web/API tests."""
    import asyncio
    import config
    import database

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setattr(config, "DB_URL", path)
    asyncio.run(database.init_db())
    yield path
    if os.path.exists(path):
        os.unlink(path)
