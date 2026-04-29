from datetime import datetime, timedelta
from typing import List
from const import TITLE_BLACKLIST, TITLE_WHITELIST
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ScrapeResult:
    """
    Data class to store scraping results
    """
    title: str
    url: str
    company_name: str
    timestamp: str


def get_company_directory() -> List[str]:
    """
    Grab list of configs from the config directory
    """
    company_names = []
    for path in Path("configs").iterdir():
        if path.is_file() and path.suffix == ".py" and path.stem != "__init__":
            company_names.append(path.stem)
    return company_names


def filter_title(title: str, strict: bool) -> bool:
    """
    Filter out irrelevant job titles
    """
    title = title.lower()
    if title.count("intern") <= title.count("interna"): return False
    if not strict: return True
    for word in TITLE_BLACKLIST:
        if word in title: return False
    for word in TITLE_WHITELIST:
        if word in title: return True
    return False


def filter_location(location_list: List[str], location: str) -> bool:
    """
    Filter job locations
    """
    location = location.lower()
    for word in location_list:
        if word in location: return True
    return False


def trim_logs() -> None:
    """
    Trim log files to last 7 days
    """
    for path in Path("logs").iterdir():
        log_date = datetime.strptime(path.stem, "scrape_%Y-%m-%d_%H-%M-%S").date()
        if log_date < datetime.now().date() - timedelta(days=7):
            path.unlink()
    
