"""
Верификация — проверка корректности бизнес-логики и функциональности.
Обращение к корню проекта: импорт database, config из C:\\Helper.
"""
from pathlib import Path

import config
import database


class TestProjectRoot:
    """Проект доступен из корня репозитория."""

    def test_project_root_contains_entry_points(self, project_root: Path):
        assert (project_root / "run.py").is_file()
        assert (project_root / "database.py").is_file()
        assert (project_root / "web" / "main.py").is_file()
        assert (project_root / "handlers").is_dir()

    def test_config_loads_from_root(self, project_root: Path):
        assert project_root.name in str(project_root)
        assert hasattr(config, "BOT_TOKEN")
        assert hasattr(config, "DB_URL")


class TestDatabaseVerification:
    """Верификация жизненного цикла тикета и ролей."""

    async def test_init_db_creates_tables(self, test_db):
        import aiosqlite

        async with aiosqlite.connect(test_db) as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ) as cur:
                tables = {row[0] for row in await cur.fetchall()}
        assert tables >= {"users", "tickets", "messages"}

    async def test_user_registration_and_role(self, test_db, monkeypatch):
        monkeypatch.setattr(config, "OWNER_ID", 999001)
        await database.create_user(999001, "owner_user", "Owner", "owner")
        assert await database.get_user_role(999001) == "owner"

        await database.create_user(100, "student", "Student")
        assert await database.get_user_role(100) == "user"

    async def test_full_ticket_lifecycle(self, test_db):
        await database.create_user(1, "u1", "User")
        await database.create_user(2, "h1", "Helper", "helper")

        ticket_id = await database.create_ticket(1, "Не работает VPN")
        ticket = await database.get_ticket(ticket_id)
        assert ticket["status"] == "waiting"

        assert await database.accept_ticket(ticket_id, 2) is True
        active = await database.get_active_ticket_by_helper(2)
        assert active["id"] == ticket_id
        assert active["status"] == "active"

        assert await database.close_ticket(ticket_id) is True
        assert await database.rate_ticket(ticket_id, 5) is True

        closed = await database.get_ticket(ticket_id)
        assert closed["status"] == "closed"
        assert closed["rating"] == 5

    async def test_message_logging(self, test_db):
        await database.create_user(1, "u", "U")
        tid = await database.create_ticket(1, "Вопрос")
        await database.log_message(tid, 1, "user", "Привет")
        stats = await database.get_db_stats()
        assert stats["total_tickets"] == 1

    async def test_stats_after_multiple_tickets(self, test_db):
        await database.create_user(1, "u", "U")
        await database.create_user(2, "h", "H", "helper")

        for i in range(3):
            tid = await database.create_ticket(1, f"Issue {i}")
            await database.accept_ticket(tid, 2)
            await database.close_ticket(tid)
            await database.rate_ticket(tid, 4 + (i % 2))

        stats = await database.get_db_stats()
        assert stats["total_tickets"] == 3
        assert stats["closed_tickets"] == 3
        assert stats["total_ratings"] == 3
        assert 4.0 <= stats["avg_rating"] <= 5.0


class TestNetworkVerification:
    """Верификация модуля сети Telegram."""

    def test_direct_check_returns_bool(self):
        from telegram_network import can_reach_telegram_direct

        result = can_reach_telegram_direct(timeout=2.0)
        assert isinstance(result, bool)

    async def test_resolve_proxy_with_explicit_config(self):
        from telegram_network import resolve_telegram_proxy

        proxy = await resolve_telegram_proxy("socks5://127.0.0.1:59999")
        assert proxy == "socks5://127.0.0.1:59999"
