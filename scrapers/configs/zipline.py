from typing import List

from playwright.sync_api import Page, TimeoutError

from models import ScrapeResult
from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


MAX_SCROLLS = 20
REQUIRED_STABLE_SCROLLS = 2
SCROLL_WAIT_MS = 1000
SCROLL_SENTINEL_SELECTOR = "[data-roles-list] > div[aria-hidden='true']"


def zipline_scrape(
    config: SimpleScrapeConfig, page: Page
) -> dict[str, List[ScrapeResult]]:
    """Load Zipline's lazy job list, then extract it with simple_scrape."""
    job_cards = page.locator(config.jobs_selector)
    try:
        job_cards.first.wait_for(state="attached", timeout=5000)
    except TimeoutError:
        return simple_scrape(config, page)

    scroll_sentinel = page.locator(SCROLL_SENTINEL_SELECTOR)
    previous_count = -1
    stable_scrolls = 0

    for _ in range(MAX_SCROLLS):
        current_count = job_cards.count()
        if current_count == previous_count:
            stable_scrolls += 1
            if stable_scrolls >= REQUIRED_STABLE_SCROLLS:
                break
        else:
            stable_scrolls = 0

        if scroll_sentinel.count() == 0:
            break

        previous_count = current_count
        scroll_sentinel.scroll_into_view_if_needed()
        page.wait_for_timeout(SCROLL_WAIT_MS)

    return simple_scrape(config, page)


config = SimpleScrapeConfig(
    company_name="zipline",
    base_url="https://www.zipline.com/open-roles?q=intern",
    jobs_selector="div[data-role-card='true']",
    url_selector="a",
    title_selector="h3",
    location_selector="div > p:nth-child(2)",
    link_augmentation=lambda url: "https://www.zipline.com" + url,
    empty_portal_selector="[data-roles-list]",
)

strategy = zipline_scrape
