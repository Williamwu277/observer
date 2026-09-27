from dataclasses import dataclass, field
from typing import Callable, Optional

from strategies.simple_scrape import SimpleScrapeConfig


ASHBY_BASE_URL = "https://jobs.ashbyhq.com"
ASHBY_EMPTY_PORTAL_SELECTOR = (
    "span.ashby-job-board-heading-count:has-text('(0)')"
)


def augment_ashby_url(url: str) -> str:
    """Turn an Ashby job path into an absolute URL."""
    return f"{ASHBY_BASE_URL}{url}"


@dataclass
class AshbyScrapeConfig(SimpleScrapeConfig):
    """Simple-scrape defaults shared by Ashby-hosted job boards."""

    jobs_selector: str = "div[class='ashby-job-posting-brief-list'] a"
    url_selector: str = ":scope"
    title_selector: str = "h3"
    link_augmentation: Optional[Callable[[str], str]] = field(
        default=augment_ashby_url,
        kw_only=True,
    )
    empty_portal_selector: Optional[str] = field(
        default=ASHBY_EMPTY_PORTAL_SELECTOR,
        kw_only=True,
    )
