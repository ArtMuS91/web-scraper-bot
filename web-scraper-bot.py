import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
from dotenv import load_dotenv

from scrapers.dou import scrape_dou

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

if not TELEGRAM_CHAT_ID:
    raise RuntimeError("TELEGRAM_CHAT_ID is not set")

TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID)

URLS = [
    {"type": "DOU", "url": "https://jobs.dou.ua/vacancies/?remote&search=бронювання"}
]

SCRAPERS = {
    "DOU": scrape_dou,
}

def scrape():
    results = []

    for entry in URLS:
        url_type = entry["type"]
        url = entry["url"]

        results.append(f"{url_type} вакансії (ремоут, з бронюванням):\n")

        scraper = SCRAPERS.get(url_type)
        if scraper is None:
            print(f"No scraper found for type '{url_type}', skipping.")
            continue

        vacancies = scraper(url)
        results.extend(v.to_html(i) for i, v in enumerate(vacancies, start=1))

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
    logging.info("Starting Telegram bot...")
    app.run_polling()
