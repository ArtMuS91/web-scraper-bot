import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
from dotenv import load_dotenv

from scrapers.djinni import scrape_djinni
from scrapers.dou import scrape_dou
from scrapers.workua import scrape_workua

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "8443"))
APP_ENV = os.getenv("APP_ENV", "production").strip().lower()

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

if not TELEGRAM_CHAT_ID:
    raise RuntimeError("TELEGRAM_CHAT_ID is not set")

if APP_ENV != "local" and not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL is not set when APP_ENV is not 'local'")

TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID)

URLS = [
    {"type": "DOU", "title": "Dou", "url": "https://jobs.dou.ua/vacancies/?remote&search=бронювання"},
    {"type": "WORKUA_REMOTE", "title": "WorkUa", "url": "https://www.work.ua/jobs-remote-it/?deferment=1&advs=1"},
    {"type": "WORKUA_KHARKIV", "title": "WorkUa", "url": "https://www.work.ua/jobs-kharkiv-it/?advs=1&deferment=1", "filter": "ремоут, Харків"},
    {"type": "DJINNI", "title": "Djinni", "url": "https://djinni.co/jobs/?search_type=basic-search&employment=remote&editorial=reservation"},
]

SCRAPERS = {
    "DOU": scrape_dou,
    "WORKUA_REMOTE": scrape_workua,
    "WORKUA_KHARKIV": scrape_workua,
    "DJINNI": scrape_djinni
}

def scrape():
    """Parse all provided URLS and prepare data for sending"""
    results = []

    for entry in URLS:
        url_type = entry["type"]
        url = entry["url"]
        title = entry["title"]
        filter = "ремоут, з бронюванням" if not entry.get("filter") else entry.get("filter")
        
        scraper = SCRAPERS.get(url_type)
        
        if scraper is None:
            print(f"No scraper found for type '{url_type}', skipping.")
            continue
        
        results.append(f"<u>{title}</u> вакансії ({filter}):\n")

        vacancies = scraper(url)
        results.extend(v.to_html(i) for i, v in enumerate(vacancies, start=1))
        results.append("\n")

    return "\n".join(results)

def allowed(update):
    return update.effective_chat.id == TELEGRAM_CHAT_ID

async def run_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not allowed(update) or update.message is None:
        return

    await update.message.reply_text(
        "⏳ Running scraper..."
    )

    result = scrape()

    await update.message.reply_text(result, parse_mode="HTML")

async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not allowed(update) or update.message is None:
        return

    await update.message.reply_text(
        "✅ Bot is running"
    )

app = Application.builder().token(
    TELEGRAM_BOT_TOKEN
).build()

app.add_handler(
    CommandHandler("run", run_command)
)

app.add_handler(
    CommandHandler("status", status)
)

if __name__ == "__main__":
    if APP_ENV == "local":
        logging.info("Starting Telegram bot via polling (local mode)...")
        app.run_polling()
    else:
        logging.info("Starting Telegram bot via webhook...")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
        )
