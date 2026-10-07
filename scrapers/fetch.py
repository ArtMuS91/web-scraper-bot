import logging
import os
import time

import requests

SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")

SCRAPERAPI_RETRY_MARKER = "multiple users connecting from your IP"
SCRAPERAPI_MAX_ATTEMPTS = 3
SCRAPERAPI_RETRY_DELAY_SECONDS = 5


def fetch(
    url: str, params=None, headers: dict | None = None, timeout: int = 20, render: bool = False
) -> requests.Response:
    """GET a page, going through ScraperAPI when SCRAPERAPI_KEY is set
    (sites that block the hosting server's IP), otherwise directly.
    render=True makes ScraperAPI load the page in a headless browser, which is needed for sites
    serving a JavaScript challenge (e.g. Imperva); it costs 10 credits per request instead of 1."""
    if not SCRAPERAPI_KEY:
        return requests.get(url, params=params, headers=headers, timeout=timeout)

    # ScraperAPI takes the target as a single url param, so bake the query string into it
    target = requests.Request("GET", url, params=params).prepare().url
    scraperapi_params = {"api_key": SCRAPERAPI_KEY, "url": target}
    if render:
        scraperapi_params["render"] = "true"
    for attempt in range(1, SCRAPERAPI_MAX_ATTEMPTS + 1):
        r = requests.get(
            "https://api.scraperapi.com",
            params=scraperapi_params,
            timeout=60,
        )
        # 5xx means ScraperAPI's own attempts failed (common on protected sites); those aren't billed
        retryable = r.status_code >= 500 or SCRAPERAPI_RETRY_MARKER in r.text
        if not retryable or attempt == SCRAPERAPI_MAX_ATTEMPTS:
            return r
        logging.warning(
            "ScraperAPI request failed for %s (status=%s, attempt %d/%d), retrying in %ds",
            target, r.status_code, attempt, SCRAPERAPI_MAX_ATTEMPTS, SCRAPERAPI_RETRY_DELAY_SECONDS,
        )
        time.sleep(SCRAPERAPI_RETRY_DELAY_SECONDS)
    raise AssertionError("unreachable")
