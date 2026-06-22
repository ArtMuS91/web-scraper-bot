import requests
from bs4 import BeautifulSoup

from models import Vacancy
from utils import parse_ua_date, date_to_string


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
        date_tag = item.select_one('.date')
        company_tag = item.select_one('.company')
        
        if not a_tag or not date_tag or not company_tag:
            continue
        
        date_text = date_tag.get_text().strip()
        parsed_date = parse_ua_date(date_text)
        
        vacancies.append(Vacancy(
            title=a_tag.get_text(),
            link=a_tag.get('href'),
            company=company_tag.get_text().strip(),
            date_text=date_to_string(parsed_date),
            date=parsed_date,
            is_hot='__hot' in item['class'],
        ))

    vacancies.sort(key=lambda v: v.date, reverse=True)
    
    return vacancies[:10]
