from datetime import datetime, timedelta
from typing import List, Callable
from pathlib import Path
from playwright.sync_api import CDPSession
from PIL import Image
import imagehash

from const import (
    TITLE_BLACKLIST,
    TITLE_WHITELIST,
    LOCATION_BLACKLIST,
    LOCATION_WHITELIST,
)
from models import ScrapeResult


def get_company_directory() -> List[str]:
    """
    Grab list of configs from the config directory
    """
    company_names = []
    for path in Path("configs").iterdir():
        if path.is_file() and path.suffix == ".py" and path.stem != "__init__":
            company_names.append(path.stem)
    return company_names


def filter_intern_title(title: str) -> bool:
    """
    Filter job for intern title
    """
    title = title.lower()
    if title.count("intern") <= title.count("interna"):
        return False
    return True


def filter_title_role(title: str) -> bool:
    """
    Filter for roles that are relevant
    """
    title = title.lower()
    for word in TITLE_BLACKLIST:
        if word in title:
            return False
    for word in TITLE_WHITELIST:
        if word in title:
            return True
    return False


def filter_location(location_list: List[str], location: str) -> bool:
    """
    Filter job locations
    """
    location = location.lower()
    for word in location_list:
        if word in location:
            return True
    return False


def filter_out_location(location_string: str) -> bool:
    """
    Returns whether or not the location string has a blacklisted location
    """
    return filter_location(LOCATION_BLACKLIST, location_string)


def filter_for_location(location_string: str) -> bool:
    """
    Returns whether or not the location string has a whitelisted location
    """
    return filter_location(LOCATION_WHITELIST, location_string)


def filter_job(job: ScrapeResult) -> bool:
    """
    Filters a job based on the title and location. Returns True if the job passes the filters
    """
    if job.location is not None:
        if not filter_for_location(job.location):
            return False

    if not filter_intern_title(job.title):
        return False

    if not filter_title_role(job.title):
        return False

    if filter_out_location(job.title):
        return False

    return True


def attach_network_monitor(cdp_session: CDPSession) -> Callable[[], int]:
    """
    Track the total bytes transferred over the wire during a scrape using the
    Chrome DevTools Protocol. This estimates how much data a residential proxy
    would need to transfer for the run.

    Returns a function that yields the current total of transferred bytes.
    """
    cdp_session.send("Network.enable")
    transferred = {"bytes": 0}

    def on_loading_finished(event: dict) -> None:
        transferred["bytes"] += event.get("encodedDataLength", 0)

    cdp_session.on("Network.loadingFinished", on_loading_finished)
    return lambda: transferred["bytes"]


def trim_logs() -> None:
    """
    Trim log files to last 7 days
    """
    for path in Path("logs").iterdir():
        log_date = datetime.strptime(path.stem, "scrape_%Y-%m-%d_%H-%M-%S").date()
        if log_date < datetime.now().date() - timedelta(days=7):
            path.unlink()


def calculate_pHash(image_path: str) -> imagehash.ImageHash:
    """
    Calculate the pHash of an image
    """
    with Image.open(image_path) as image:
        return imagehash.phash(image)
