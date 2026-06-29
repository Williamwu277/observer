import logging

from playwright.sync_api import Page
from typing import List, Any, Callable
from random import uniform

from models import ScrapeConfig, ScrapeResult
from utils import filter_job


logger = logging.getLogger(__name__)


def scrape_integration(
    config: ScrapeConfig, strategy: Callable, page: Page
) -> List[ScrapeResult]:
    """
    Scraping framework to scrape a given integration
    """
    scrape_context = {"config": config, "page": page}

    states = [
        {"state": "NAVIGATING_TO_PORTAL", "action": navigate_to_portal},
        {"state": "FINDING_JOBS", "action": strategy},
        {"state": "FILTERING_JOBS", "action": filter_jobs},
    ]

    for state in states:
        # Don't try/except here because we want to catch in scrape.py
        logger.info(f"Starting state: [{state['state']}]")
        result = state["action"](**scrape_context)
        scrape_context = {**scrape_context, **result}
        logger.info(f"Finished state: [{state['state']}]")

    return scrape_context["jobs"]


def navigate_to_portal(config: ScrapeConfig, page: Page) -> dict:
    """
    Navigate to the portal
    """
    logger.info(f"Navigating to: {config.base_url}")
    page.goto(config.base_url, referer="https://www.google.com/")
    page.wait_for_timeout(uniform(1000, 3000))

    if config.cookies_accept_text:
        page.get_by_role("button", name=config.cookies_accept_text).first.click()
        page.wait_for_timeout(uniform(1000, 3000))

    return {}


def filter_jobs(jobs: List[ScrapeResult], **_: Any) -> dict[str, List[ScrapeResult]]:
    """
    Filter the jobs. Returns a dictionary of the form:
    {
        "jobs": List[ScrapeResult]
    }
    """
    filtered_jobs = list(filter(lambda job: filter_job(job), jobs))
    logger.info(f"Found {len(filtered_jobs)} jobs after filtering")
    return {"jobs": list(filtered_jobs)}
