"""
Юзабилити — доступность API, понятность интерфейсов, UX-контракты.
"""
from pathlib import Path

import config
from fastapi.testclient import TestClient
from web.main import app


class TestWebUsability:
    def test_dashboard_returns_html_in_russian(self, test_db_sync):
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        body = response.text
        assert "IT Top" in body or "поддерж" in body.lower() or "тикет" in body.lower()

    def test_widget_page_loads(self, test_db_sync):
        client = TestClient(app)
        response = client.get("/widget")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_api_rating_json_contract(self, test_db_sync):
        client = TestClient(app)
        data = client.get("/api/rating").json()
        assert data["success"] is True
        assert "rating" in data
        assert "total_reviews" in data
        assert isinstance(data["rating"], (int, float))

    def test_api_stats_json_contract(self, test_db_sync):
        client = TestClient(app)
        data = client.get("/api/stats").json()
        required = {
            "total_tickets",
            "active_tickets",
            "waiting_tickets",
            "closed_tickets",
            "avg_rating",
            "total_ratings",
            "ratings_distribution",
            "helpers",
        }
        assert required.issubset(data.keys())
        assert set(map(int, data["ratings_distribution"].keys())) == {1, 2, 3, 4, 5}

    def test_static_css_available(self, project_root: Path):
        css = project_root / "web" / "static" / "css" / "style.css"
        assert css.is_file()
        client = TestClient(app)
        response = client.get("/static/css/style.css")
        assert response.status_code == 200

    def test_cors_allows_widget_embed(self):
        client = TestClient(app)
        response = client.get(
            "/api/rating",
            headers={"Origin": "https://online.top-academy.ru"},
        )
        assert response.status_code == 200


class TestBotUsability:
    """Проверка UX-элементов бота (клавиатуры, тексты)."""

    def test_main_menu_has_ticket_button(self):
        from handlers.user import get_main_menu_keyboard

        kb = get_main_menu_keyboard("user")
        labels = [btn.text for row in kb.keyboard for btn in row]
        assert "🎫 Создать тикет" in labels

    def test_helper_menu_shows_admin_panel(self):
        from handlers.user import get_main_menu_keyboard

        kb = get_main_menu_keyboard("helper")
        labels = [btn.text for row in kb.keyboard for btn in row]
        assert "⚙️ Панель управления" in labels

    def test_rating_keyboard_has_five_options(self):
        from handlers.user import get_rating_keyboard

        kb = get_rating_keyboard(42)
        assert len(kb.inline_keyboard[0]) == 5
        for btn in kb.inline_keyboard[0]:
            assert btn.callback_data.startswith("rate:42:")

    def test_helper_panel_keyboard(self):
        from handlers.helper import get_helper_menu

        kb = get_helper_menu()
        labels = [btn.text for row in kb.keyboard for btn in row]
        assert any("ожидания" in l.lower() for l in labels)


class TestStartupUsability:
    def test_check_deps_from_project_root(self, project_root: Path):
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, str(project_root / "check_deps.py")],
            cwd=str(project_root),
            capture_output=True,
        )
        assert result.returncode == 0

    def test_start_bat_exists(self, project_root: Path):
        assert (project_root / "start.bat").is_file()

    def test_requirements_lists_core_packages(self, project_root: Path):
        text = (project_root / "requirements.txt").read_text(encoding="utf-8")
        for pkg in ("aiogram", "fastapi", "aiosqlite"):
            assert pkg in text
