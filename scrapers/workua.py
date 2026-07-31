import logging
import os
import time
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

from models import Vacancy
from utils import date_to_string

SKIP_COMPANIES = ["Nix"]

SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.work.ua/",
}

SCRAPERAPI_RETRY_MARKER = "multiple users connecting from your IP"
SCRAPERAPI_MAX_ATTEMPTS = 3
SCRAPERAPI_RETRY_DELAY_SECONDS = 5

def scrape_workua(url: str) -> list[Vacancy]:
    if SCRAPERAPI_KEY:
        r = requests.get(
            "https://api.scraperapi.com",
            params={"api_key": SCRAPERAPI_KEY, "url": url},
            timeout=60,
        )
        for attempt in range(2, SCRAPERAPI_MAX_ATTEMPTS + 1):
            if SCRAPERAPI_RETRY_MARKER not in r.text:
                break
            logging.warning(
                "ScraperAPI concurrency limit hit for %s (attempt %d/%d), retrying in %ds",
                url, attempt - 1, SCRAPERAPI_MAX_ATTEMPTS, SCRAPERAPI_RETRY_DELAY_SECONDS,
            )
            time.sleep(SCRAPERAPI_RETRY_DELAY_SECONDS)
            r = requests.get(
                "https://api.scraperapi.com",
                params={"api_key": SCRAPERAPI_KEY, "url": url},
                timeout=60,
            )
    else:
        r = requests.get(
            url,
            timeout=20,
            headers=HEADERS,
        )

    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select('.job-link')
    if not items:
        logging.error(
            "WorkUa scraper got no '.job-link' items for %s (status=%s, final_url=%s, len=%d). "
            "First 300 chars: %r",
            url, r.status_code, r.url, len(r.text), r.text[:300],
        )

    vacancies: list[Vacancy] = []
    for item in items:
        a_tag = item.select_one('h2 a')
        date_tag = item.select_one('time')
        company_tag = item.select_one('.strong-600')
        
        if not a_tag or not company_tag:
            continue
        
        company = company_tag.get_text().strip()
        
        if company in SKIP_COMPANIES:
            continue
        
        parsed_date = date.today() if not date_tag else datetime.fromisoformat(str(date_tag.get('datetime'))).date()
        
        vacancies.append(Vacancy(
            title=a_tag.get_text(),
            link=f"https://www.work.ua{a_tag.get('href')}",
            company=company,
            date_text=date_to_string(parsed_date),
            date=parsed_date,
            is_hot='js-hot-block' in item['class'],
        ))

    vacancies.sort(key=lambda v: v.date, reverse=True)
    return vacancies[:10]
