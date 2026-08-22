from dataclasses import dataclass, field
from enum import Enum
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
    # Used for filtering. Only necessary if location can be global
    location_selector: Optional[str] = field(default=None, kw_only=True)
    # If the scraped url is relative, use this function to make it complete
    link_augmentation: Optional[Callable[[str], str]] = field(
        default=None, kw_only=True
    )
    cookies_accept_text: Optional[str] = field(default=None, kw_only=True)
    # Experimental: element to screenshot when the portal returns zero jobs,
    # enabling first-class detection of portal changes via perceptual hashing
    empty_portal_selector: Optional[str] = field(default=None, kw_only=True)


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


class ScrapeStatus(Enum):
    """
    Health status of a scraping integration.

    Operational scrapers find jobs. Questionable scrapers find no jobs and await
    human verification. Confident scrapers have a human-verified empty portal.
    Down scrapers are erroring or failed empty-portal change detection.
    """

    OPERATIONAL = "Operational"
    CONFIDENT = "Confident"
    QUESTIONABLE = "Questionable"
    DOWN = "Down"


@dataclass
class StatusResult:
    """
    Data class to store the health of a scraping integration for a single run
    """

    company_name: str
    portal_url: str
    status: ScrapeStatus
    last_updated: str
    # How long the scrape took in seconds
    scrape_time: float
    # Megabytes transferred over the wire during the scrape
    request_size: float
    # Any error occuring during the scrape. Usually broadcasted using the discord integration
    error: Optional[str] = field(default=None, kw_only=True)
    # Hex string of the perceptual hash of the empty-portal screenshot.
    # "0" is the sentinel for "no baseline recorded yet"
    pHash: Optional[str] = field(default="0", kw_only=True)
