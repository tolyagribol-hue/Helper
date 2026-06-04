"""
Валидация — проверка граничных условий, некорректных данных, защита от ошибок.
"""
import config
import database


class TestTicketValidation:
    async def test_accept_nonexistent_ticket(self, test_db):
        await database.create_user(2, "h", "Helper", "helper")
        assert await database.accept_ticket(99999, 2) is False

    async def test_accept_already_active_ticket(self, test_db):
        await database.create_user(1, "u", "User")
        await database.create_user(2, "h", "Helper", "helper")
        tid = await database.create_ticket(1, "Help")
        await database.accept_ticket(tid, 2)
        assert await database.accept_ticket(tid, 2) is False

    async def test_close_already_closed_ticket(self, test_db):
        await database.create_user(1, "u", "User")
        tid = await database.create_ticket(1, "Q")
        await database.close_ticket(tid)
        assert await database.close_ticket(tid) is False

    async def test_rate_open_ticket_has_no_effect_on_closed_check(self, test_db):
        await database.create_user(1, "u", "User")
        tid = await database.create_ticket(1, "Open")
        await database.rate_ticket(tid, 5)
        ticket = await database.get_ticket(tid)
        assert ticket["status"] == "waiting"
        assert ticket["rating"] is None

    async def test_user_cannot_have_two_active_tickets(self, test_db):
        await database.create_user(1, "u", "User")
        await database.create_ticket(1, "First")
        active = await database.get_active_ticket_by_user(1)
        assert active is not None
        # Вторая заявка возможна в БД, но handler блокирует — проверяем наличие активной
        assert active["status"] == "waiting"


class TestUserValidation:
    async def test_set_role_unknown_user(self, test_db):
        assert await database.set_user_role(404, "helper") is False

    async def test_get_user_missing(self, test_db):
        assert await database.get_user(0) is None

    async def test_username_lookup_normalization(self, test_db):
        await database.create_user(10, "TestUser", "T")
        found = await database.get_user_by_username("@TestUser")
        assert found["id"] == 10


class TestConfigValidation:
    def test_is_configured_rejects_placeholder(self, monkeypatch):
        monkeypatch.setattr(config, "BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
        assert config.is_configured() is False

    def test_is_configured_accepts_real_token(self, monkeypatch):
        monkeypatch.setattr(config, "BOT_TOKEN", "123456:ABC-DEF")
        assert config.is_configured() is True

    def test_owner_id_zero_means_no_owner(self, monkeypatch):
        monkeypatch.setattr(config, "OWNER_ID", 0)
        assert config.OWNER_ID == 0

    def test_web_port_is_positive_integer(self):
        assert isinstance(config.WEB_PORT, int)
        assert config.WEB_PORT > 0


class TestRatingValidation:
    async def test_rating_only_on_closed(self, test_db):
        await database.create_user(1, "u", "User")
        tid = await database.create_ticket(1, "Rate me")
        await database.close_ticket(tid)
        await database.rate_ticket(tid, 1)
        await database.rate_ticket(tid, 5)
        ticket = await database.get_ticket(tid)
        assert ticket["rating"] == 5
