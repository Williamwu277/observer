from dataclasses import dataclass
from typing import Optional


@dataclass
class ScrapeConfig:
    """
    Config class to store scraping data for each integration
    """
    company_name: str
    base_url: str


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