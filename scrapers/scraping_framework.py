import logging

from enum import Enum
from random import uniform
from typing import Any, Callable, List

from playwright.sync_api import Page

from models import ScrapeConfig, ScrapeResult, NoJobsFoundError
from utils import filter_job


logger = logging.getLogger(__name__)


class ScrapeState(Enum):
    NAVIGATING_TO_PORTAL = "NAVIGATING_TO_PORTAL"
    FINDING_JOBS = "FINDING_JOBS"
    POST_SCRAPE_ACTION = "POST_SCRAPE_ACTION"
    FILTERING_JOBS = "FILTERING_JOBS"


def scrape_integration(
    config: ScrapeConfig, strategy: Callable, page: Page
) -> List[ScrapeResult]:
    """
    Scraping framework to scrape a given integration
    Acts as a state machine running the correct action for each state.
    """
    scrape_context = {"config": config, "page": page}

    states = [
        {"state": ScrapeState.NAVIGATING_TO_PORTAL, "action": navigate_to_portal},
        {"state": ScrapeState.FINDING_JOBS, "action": strategy},
        {"state": ScrapeState.POST_SCRAPE_ACTION, "action": post_scrape_action},
        {"state": ScrapeState.FILTERING_JOBS, "action": filter_jobs},
    ]

    for state in states:
        # Don't try/except here because we want to catch in scrape.py
        logger.info(f"Starting state: [{state['state'].value}]")
        result = state["action"](**scrape_context)
        scrape_context = {"config": config, "page": page, **result}
        logger.info(f"Finished state: [{state['state'].value}]")

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


def post_scrape_action(
    config: ScrapeConfig, page: Page, jobs: List[ScrapeResult], **_: Any
) -> dict:
    """
    If the portal has no jobs, take a screenshot at the empty_portal_selector
    """
    if len(jobs) > 0:
        return {"jobs": jobs}

    if config.empty_portal_selector is None:
        raise NoJobsFoundError(f"No jobs found for {config.company_name}")

    logger.info(f"Taking a screenshot of {config.company_name} portal to check for changes")

    page.wait_for_timeout(uniform(500, 1000))

    # Scroll the anchor into view, then capture just the viewport. The viewport
    # is fixed, so the screenshot stays comparable between runs for hashing.
    # If this element isn't found, then the portal has changed
    empty_portal_element = page.locator(config.empty_portal_selector).first
    empty_portal_element.scroll_into_view_if_needed()
    page.screenshot(path=f"tmp/{config.company_name}.png")

    raise NoJobsFoundError(f"No jobs found for {config.company_name}")


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
