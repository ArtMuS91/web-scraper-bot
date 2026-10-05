import logging
from datetime import date, datetime
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup

from models import Vacancy
from utils import date_to_string

BASE_URL = "https://career.intellias.com"
AJAX_URL = f"{BASE_URL}/wp-admin/admin-ajax.php"
REST_URL = f"{BASE_URL}/wp-json/wp/v2/vacancy"
MAX_PAGES = 10
# checkbox filters sent as a single value (filter[remote]=on), the rest are arrays (filter[location][]=...)
FLAG_FILTERS = {"hot", "remote", "office", "hybrid"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}


def parse_filters(url: str) -> list[tuple[str, str]]:
    """Convert a page URL like /vacancies/job-profile_net-engineer-or-qa-and-location_ukraine/search/react/
    into the form data the site's filter script posts to admin-ajax.php:
    filter[job-profile][]=net-engineer&filter[job-profile][]=qa&filter[location][]=ukraine&search=react"""
    parts = [unquote(p) for p in urlparse(url).path.split("/") if p]
    parts = parts[parts.index("vacancies") + 1:]

    params: list[tuple[str, str]] = []
    if "search" in parts:
        search_index = parts.index("search")
        if search_index + 1 < len(parts):
            params.append(("search", parts[search_index + 1].replace("_", " ")))
        parts = parts[:search_index]

    for group in (parts[0].split("-and-") if parts else []):
        key, sep, values = group.partition("_")
        if not sep:
            continue
        if key in FLAG_FILTERS:
            params.append((f"filter[{key}]", values))
        else:
            params.extend((f"filter[{key}][]", v) for v in values.split("-or-"))

    return params


def fetch_cards(params: list[tuple[str, str]]) -> list[BeautifulSoup]:
    cards = []
    for page in range(1, MAX_PAGES + 1):
        r = requests.post(
            AJAX_URL,
            data=[("action", "fly_vacancies"), ("page", str(page)), *params],
            timeout=20,
            headers=HEADERS,
        )
        r.raise_for_status()
        payload = r.json()

        for post in payload["posts"]:
            card = BeautifulSoup(post, "html.parser").select_one("a.card_item")
            if card:
                cards.append(card)

        if payload["end"]:
            break
    return cards


def fetch_dates(slugs: list[str]) -> dict[str, date]:
    """Cards have no publish date, so look them up in bulk via the WordPress REST API"""
    dates: dict[str, date] = {}
    for i in range(0, len(slugs), 100):
        r = requests.get(
            REST_URL,
            params=[("per_page", "100"), ("_fields", "slug,date"), *(("slug[]", s) for s in slugs[i:i + 100])],
            timeout=20,
            headers=HEADERS,
        )
        r.raise_for_status()
        for item in r.json():
            dates[item["slug"]] = datetime.fromisoformat(item["date"]).date()
    return dates


def scrape_intellias(url: str) -> list[Vacancy]:
    params = parse_filters(url)
    cards = fetch_cards(params)

    if not cards:
        logging.warning("Intellias scraper got no vacancies for %s (params=%s)", url, params)
        return []

    def slug(card) -> str:
        return str(card.get("href")).rstrip("/").rsplit("/", 1)[-1]

    dates = fetch_dates([slug(card) for card in cards])

    vacancies: list[Vacancy] = []
    for card in cards:
        title_tag = card.select_one(".card_title")
        if not title_tag:
            continue

        parsed_date = dates.get(slug(card), date.min)

        vacancies.append(Vacancy(
            title=title_tag.get_text().strip(),
            link=str(card.get("href")),
            company="Intellias",
            date_text=date_to_string(parsed_date) if parsed_date != date.min else "",
            date=parsed_date,
            is_hot=card.select_one(".hot img") is not None,
        ))

    vacancies.sort(key=lambda v: v.date, reverse=True)
    return vacancies[:10]
