# web-scraper-bot

A Telegram bot that scrapes job vacancies from [dou.ua](https://jobs.dou.ua/vacancies),
[work.ua](https://www.work.ua/), [djinni.co](https://djinni.co/jobs) and the career sites of custom companies,
then sends a formatted digest to a Telegram chat on demand.

## Features

- Scrapes vacancies from job boards and custom company career sites, each with its own configurable search URL and filter label
- Parses Ukrainian-language dates and sorts vacancies by date (newest first)
- Highlights "hot" vacancies with a 🔥 icon
- Sends results as an HTML-formatted Telegram message
- Responds only to the configured chat via `/run` and `/status` commands
- Runs with polling locally and via webhook in production

## Project Structure

```
web-scraper-bot.py   # Entry point — Telegram bot, URL/scraper registry, digest builder
models.py            # Vacancy dataclass with HTML rendering
utils.py             # Ukrainian date parser and date formatting helpers
requirements.txt     # Python dependencies
scrapers/
  dou.py             # dou.ua scraper
  workua.py          # work.ua scraper
  djinni.py          # djinni.co scraper
  <company>.py       # Custom company scrapers (one file per company career site)
tests/
  test_core.py       # Unit tests for models, utils and bot helpers
.github/workflows/
  tests.yml          # CI: runs pytest on pull requests and pushes to main
```

Custom company scrapers translate the career site's page URL (with its filters) into requests
to the site's own API and map the results to `Vacancy` objects.

## Requirements

- Python 3.10+
- Dependencies: `requests`, `beautifulsoup4`, `python-telegram-bot[webhooks]`, `python-dotenv`, `pytest`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
WEBHOOK_URL=your_webhook_url_here
PORT=8443
APP_ENV=local
SCRAPERAPI_KEY=your_scraperapi_key_here
```

| Variable | Description |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather (required) |
| `TELEGRAM_CHAT_ID` | The only chat the bot responds to (required) |
| `WEBHOOK_URL` | Public webhook URL (required unless `APP_ENV=local`) |
| `PORT` | Port for the webhook server (default `8443`) |
| `APP_ENV` | `local` uses polling; any other value (default `production`) uses a webhook |
| `SCRAPERAPI_KEY` | Optional [ScraperAPI](https://www.scraperapi.com/) key used by the work.ua and some custom scrapers (see below) |

### Why `SCRAPERAPI_KEY`

work.ua and some custom (behind Imperva bot protection) block direct requests from the hosting server: work.ua
returns pages with no vacancies, custom career stire returns a non-JSON challenge page. When `SCRAPERAPI_KEY` is set, these
scrapers send their requests through ScraperAPI (`scrapers/fetch.py`) to get around the block.
If ScraperAPI fails with a 5xx error (common for protected sites, and not billed) or replies that too many users
are connecting from the same IP (its concurrency limit), the request waits 5 seconds and tries again, up to
3 attempts in total. Without the key, the sites are requested directly, which usually works fine when running locally.

## Deployment

This project is hosted on [Render](https://render.com/) and is configured to deploy automatically whenever changes are merged into the `main` branch.

## Testing

Run the test suite locally with:

```bash
pytest
```

GitHub Actions runs the tests on every pull request and push to `main`, and blocks merging if any test fails.

## Usage

```bash
python web-scraper-bot.py
```

Then send commands to the bot from the configured chat:

- `/run` — scrapes each configured URL, builds an HTML digest, and replies with it
- `/status` — confirms the bot is running

## Adding More Scrapers

1. Create a new file under `scrapers/` with a function that takes a URL and returns a `list[Vacancy]`.
2. Import it and register it in the `SCRAPERS` dict in `web-scraper-bot.py`.
3. Add an entry to the `URLS` list with the matching `type` key, a `title`, the `url`, and an optional
   `filter` label shown in the digest header (defaults to `ремоут, з бронюванням`).

