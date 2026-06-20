# web-scraper-bot

A Python bot that scrapes job vacancies from [dou.ua](https://jobs.dou.ua/vacancies),
[work.ua](https://www.work.ua/), [djinni.co](https://djinni.co/jobs) and sends a formatted digest to a Telegram chat.

## Features

- Scrapes remote vacancies from provided urls with a configurable search query
- Parses Ukrainian-language dates and sorts vacancies by date (newest first)
- Highlights "hot" vacancies with a 🔥 icon
- Sends results as an HTML-formatted Telegram message

## Project Structure

```
web-scraper-bot.py   # Entry point — orchestrates scraping and Telegram delivery
models.py            # Vacancy dataclass with HTML rendering
utils.py             # Ukrainian date parser
scrapers/
  dou.py             # dou.ua scraper
  workua.py          # work.ua scraper
  djinni.py          # djinni.co scraper
```

## Requirements

- Python 3.10+
- Dependencies: `requests`, `beautifulsoup4`, `python-telegram-bot`, `python-dotenv`

Install dependencies:

```bash
pip install requests beautifulsoup4 python-telegram-bot python-dotenv
```

## Configuration

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
WEBHOOK_URL=your_webhook_url_here
PORT=8443
APP_ENV=local
```

## Deployment

This project is hosted on [Render](https://render.com/) and is configured to deploy automatically whenever changes are merged into the `main` branch.

## Usage

```bash
python web-scraper-bot.py
```

The script scrapes each configured URL, builds an HTML digest, and sends it to the configured Telegram chat.

## Adding More Scrapers

1. Create a new file under `scrapers/` that returns a `list[Vacancy]`.
2. Register the scraper in the `SCRAPERS` dict in `web-scraper-bot.py`.
3. Add an entry to the `URLS` list with the matching `type` key.

