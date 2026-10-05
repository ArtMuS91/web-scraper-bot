import logging
from datetime import date, datetime

from bs4 import BeautifulSoup

from models import Vacancy
from scrapers.fetch import fetch
from utils import date_to_string

SKIP_COMPANIES = ["Nix"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.work.ua/",
}

def scrape_workua(url: str) -> list[Vacancy]:
    r = fetch(url, headers=HEADERS)

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
