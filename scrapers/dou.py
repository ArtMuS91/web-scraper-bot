import requests
from bs4 import BeautifulSoup

from models import Vacancy
from utils import parse_ua_date


def scrape_dou(url: str) -> list[Vacancy]:
    r = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "Google Chrome"}
    )

    soup = BeautifulSoup(r.text, "html.parser")

    vacancies: list[Vacancy] = []
    for item in soup.select('.l-vacancy'):
        a_tag = item.select_one('a.vt')
        date_text = item.select_one('.date').get_text().strip()
        vacancies.append(Vacancy(
            title=a_tag.get_text(),
            link=a_tag.get('href'),
            company=item.select_one('.company').get_text().strip(),
            date_text=date_text,
            date=parse_ua_date(date_text),
            is_hot='__hot' in item['class'],
        ))

    vacancies.sort(key=lambda v: v.date, reverse=True)
    return vacancies
