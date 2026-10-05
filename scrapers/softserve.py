import logging
from datetime import date
from urllib.parse import unquote, urlparse

import requests

from models import Vacancy

BASE_URL = "https://career.softserveinc.com"
API_URL = f"{BASE_URL}/api/frontend/vacancies"
MAX_PAGES = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def parse_filters(url: str) -> tuple[str, list[tuple[str, str]]]:
    """Convert a page URL like /uk-ua/vacancies/country-ukraine/position-senior,lead/q-Net%20react
    into the locale prefix and the query params the site's frontend sends to the API:
    country[]=ukraine&position[]=senior&position[]=lead&q=Net react"""
    parts = [unquote(p) for p in urlparse(url).path.split("/") if p]
    vacancies_index = parts.index("vacancies")
    locale = "/".join(parts[:vacancies_index])

    params: list[tuple[str, str]] = []
    for segment in parts[vacancies_index + 1:]:
        key, sep, value = segment.partition("-")
        if not sep:
            continue
        if key == "q":
            params.append(("q", value))
        else:
            params.extend((f"{key}[]", v) for v in value.split(","))

    return locale, params


def scrape_softserve(url: str) -> list[Vacancy]:
    locale, params = parse_filters(url)

    items: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        r = requests.get(
            API_URL,
            params=[*params, ("page", str(page))],
            timeout=20,
            headers=HEADERS,
        )
        r.raise_for_status()
        payload = r.json()

        items.extend(payload["data"]["vacancies"])
        if page >= payload["meta"]["last_page"]:
            break

    if not items:
        logging.warning("SoftServe scraper got no vacancies for %s (params=%s)", url, params)

    # API exposes no publish date; ids are sequential, so the highest id is the newest
    items.sort(key=lambda v: v["id"], reverse=True)

    link_prefix = f"{BASE_URL}/{locale}/vacancies" if locale else f"{BASE_URL}/vacancies"
    return [
        Vacancy(
            title=item["name"].strip(),
            link=f"{link_prefix}/{item['urlSegment']}",
            company="SoftServe",
            date_text=", ".join(filter(None, [(item.get("level") or {}).get("name"), item.get("city")])),
            date=date.today(),
        )
        for item in items[:10]
    ]
