from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

from models import Vacancy
from utils import date_to_string

SKIP_COMPANIES = ["Nix"]

def scrape_workua(url: str) -> list[Vacancy]:
    r = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "Google Chrome"}
    )

    soup = BeautifulSoup(r.text, "html.parser")

    vacancies: list[Vacancy] = []
    for item in soup.select('.job-link'):
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
