import asyncio
import os
from telegram import Bot
from dotenv import load_dotenv

from scrapers.dou import scrape_dou

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

async def send_to_telegram(text):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=text,
        parse_mode="HTML"
    )

async def main():
    data = scrape()
    # print(data)
    await send_to_telegram(data)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
