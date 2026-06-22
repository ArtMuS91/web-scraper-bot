import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

from models import Vacancy
from utils import date_to_string

def scrape_djinni(url: str) -> list[Vacancy]:
    r = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "Google Chrome"}
    )

    soup = BeautifulSoup(r.text, "html.parser")

    vacancies: list[Vacancy] = []
    for item in soup.select('.job-item'):
        a_tag = item.select_one('.job_item__header-link')
        company_tag = a_tag.select_one('.small.text-gray-800.opacity-75.font-weight-500') if a_tag else None
        title_tag = a_tag.select_one('h2.job-item__position') if a_tag else None

        if not a_tag or not company_tag or not title_tag:
            continue

        date_tag = None
        for candidate in item.select('[data-bs-original-title], [title]'):
            raw_date = str(
                candidate.get('data-bs-original-title') or candidate.get('title') or ''
            ).strip()
            if re.fullmatch(r'\d{1,2}:\d{2} \d{1,2}\.\d{1,2}\.\d{4}', raw_date):
                date_tag = candidate
                break

        if not date_tag:
            continue

        raw_date = str(
            date_tag.get('data-bs-original-title') or date_tag.get('title') or ''
        ).strip()
        parsed_date = datetime.strptime(raw_date, '%H:%M %d.%m.%Y').date()

        vacancies.append(Vacancy(
            title=title_tag.get_text(),
            link=f"https://djinni.co{a_tag.get('href')}",
            company=company_tag.get_text().strip(),
            date_text=date_to_string(parsed_date),
            date=parsed_date
        ))

    vacancies.sort(key=lambda v: v.date, reverse=True)
    return vacancies[:10]
