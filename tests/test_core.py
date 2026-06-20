import importlib.util
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models import Vacancy
from utils import date_to_string, parse_ua_date

SCRIPT_PATH = ROOT / "web-scraper-bot.py"


@pytest.fixture
def bot_module(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.com/webhook")
    monkeypatch.setenv("APP_ENV", "local")

    spec = importlib.util.spec_from_file_location("bot_module", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_parse_ua_date_parses_expected_day_and_month():
    parsed = parse_ua_date("25 березня")

    assert parsed.day == 25
    assert parsed.month == 3

def test_date_to_string_formats_date():
    assert date_to_string(date(2024, 5, 7)) == "07.05.2024"

def test_vacancy_to_html_includes_hot_icon_and_link():
    vacancy = Vacancy(
        title="Python Developer",
        link="https://example.com/job/1",
        company="Example Corp",
        date_text="01.01.2024",
        date=date(2024, 1, 1),
        is_hot=True,
    )

    html = vacancy.to_html(2)

    assert '2. 🔥' in html
    assert '<a href="https://example.com/job/1">Python Developer</a>' in html
    assert "Example Corp" in html

def test_allowed_checks_effective_chat_id(bot_module):
    matching = SimpleNamespace(effective_chat=SimpleNamespace(id=42))
    different = SimpleNamespace(effective_chat=SimpleNamespace(id=99))

    assert bot_module.allowed(matching) is True
    assert bot_module.allowed(different) is False
