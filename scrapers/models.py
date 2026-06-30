from dataclasses import dataclass, field
from typing import Callable, Optional


class NoJobsFoundError(Exception):
    """
    Raised when a scrape completes without erroring but finds zero jobs.
    Used to distinguish a "Questionable" scraper from a "Down" one.
    """


@dataclass
class ScrapeConfig:
    """
    Config class to store scraping data for each integration
    """

    company_name: str
    base_url: str
    jobs_selector: str
    url_selector: str
    title_selector: str
    # Only necessary if location can be global
    location_selector: Optional[str] = field(default=None, kw_only=True)
    # If the scraped url is relative
    link_augmentation: Optional[Callable[[str], str]] = field(
        default=None, kw_only=True
    )
    cookies_accept_text: Optional[str] = field(default=None, kw_only=True)


@dataclass
class ScrapeResult:
    """
    Data class to store scraping results
    """

    company_name: str
    url: str
    title: str
    location: Optional[str] = ""
    timestamp: Optional[str] = ""


@dataclass
class StatusResult:
    """
    Data class to store the health of a scraping integration for a single run
    """

    company_name: str
    portal_url: str
    status: str
    last_updated: str  # When the integration was last checked
    scrape_time: float  # How long the scrape took in seconds
    request_size: float  # Megabytes transferred over the wire during the scrape
    error: Optional[str] = field(default=None, kw_only=True)
