import logging

from enum import Enum
from random import uniform
from types import ModuleType
from typing import Any, Callable, List

from playwright.sync_api import Page

from models import (
    BrowserScrapeConfig,
    GreenhouseScrapeConfig,
    NoJobsFoundError,
    ScrapeResult,
)
from resource_manager import ResourceManager
from utils import filter_job


logger = logging.getLogger(__name__)
API_TIMEOUT_SECONDS = 30


class ScrapeState(Enum):
    NAVIGATING_TO_PORTAL = "NAVIGATING_TO_PORTAL"
    REQUESTING_API = "REQUESTING_API"
    FINDING_JOBS = "FINDING_JOBS"
    POST_SCRAPE_ACTION = "POST_SCRAPE_ACTION"
    FILTERING_JOBS = "FILTERING_JOBS"


def scrape_integration(
    integration: ModuleType, resources: ResourceManager
) -> List[ScrapeResult]:
    """
    Run the pipeline appropriate for an integration's config type.
    """
    config = integration.config
    strategy = integration.strategy
    resources.reset_transferred_bytes()

    if isinstance(config, BrowserScrapeConfig):
        return scrape_browser_integration(config, strategy, resources)
    if isinstance(config, GreenhouseScrapeConfig):
        return scrape_api_integration(config, strategy, resources)

    raise TypeError(f"Unsupported scrape config: {type(config).__name__}")


def scrape_browser_integration(
    config: BrowserScrapeConfig,
    strategy: Callable,
    resources: ResourceManager,
) -> List[ScrapeResult]:
    """
    Run navigation, extraction, empty-page handling, and filtering.
    """
    with resources.browser_page() as page:
        scrape_context = {"config": config, "page": page}
        states = [
            (ScrapeState.NAVIGATING_TO_PORTAL, navigate_to_portal),
            (ScrapeState.FINDING_JOBS, strategy),
            (ScrapeState.POST_SCRAPE_ACTION, post_scrape_action),
            (ScrapeState.FILTERING_JOBS, filter_jobs),
        ]
        return run_states(states, scrape_context)["jobs"]


def scrape_api_integration(
    config: GreenhouseScrapeConfig,
    strategy: Callable,
    resources: ResourceManager,
) -> List[ScrapeResult]:
    """
    Request, parse, and filter a Greenhouse API feed.
    """
    scrape_context = {"config": config, "resources": resources}
    states = [
        (ScrapeState.REQUESTING_API, request_api),
        (ScrapeState.FINDING_JOBS, strategy),
        (ScrapeState.FILTERING_JOBS, filter_jobs),
    ]
    return run_states(states, scrape_context)["jobs"]


def run_states(states: list[tuple[ScrapeState, Callable]], context: dict) -> dict:
    """
    Run a pipeline while forwarding each state's returned values.
    """
    for state, action in states:
        logger.info("Starting state: [%s]", state.value)
        result = action(**context)
        context = {**context, **result}
        logger.info("Finished state: [%s]", state.value)
    return context


def navigate_to_portal(config: BrowserScrapeConfig, page: Page) -> dict:
    """
    Navigate to a browser integration's careers portal.
    """
    logger.info("Navigating to: %s", config.base_url)
    page.goto(config.base_url, referer="https://www.google.com/")
    page.wait_for_timeout(uniform(1000, 3000))

    if config.cookies_accept_text:
        page.get_by_role("button", name=config.cookies_accept_text).first.click()
        page.wait_for_timeout(uniform(1000, 3000))

    return {}


def request_api(
    config: GreenhouseScrapeConfig, resources: ResourceManager, **_: Any
) -> dict:
    """
    Make one API request and return its decoded JSON payload.
    """
    logger.info("Requesting API: %s", config.api_url)
    response = resources.get_http_client().get(
        config.api_url,
        timeout=API_TIMEOUT_SECONDS,
    )
    resources.record_api_response(response)
    if not response.ok:
        raise RuntimeError(
            f"{config.company_name} API returned HTTP {response.status_code}"
        )
    return {"payload": response.json()}


def post_scrape_action(
    config: BrowserScrapeConfig,
    page: Page,
    jobs: List[ScrapeResult],
    **_: Any,
) -> dict:
    """
    Capture browser evidence when a portal returns no jobs.
    """
    if jobs:
        return {"jobs": jobs}

    if config.empty_portal_selector is None:
        raise NoJobsFoundError(f"No jobs found for {config.company_name}")

    logger.info(
        "Taking a screenshot of %s portal to check for changes", config.company_name
    )
    page.wait_for_timeout(uniform(500, 1000))

    # Scroll the anchor into view, then capture just the viewport. The viewport
    # is fixed, so the screenshot stays comparable between runs for hashing.
    # If this element isn't found, then the portal has changed.
    empty_portal_element = page.locator(config.empty_portal_selector).first
    empty_portal_element.scroll_into_view_if_needed()
    page.screenshot(path=f"tmp/{config.company_name}.png")

    raise NoJobsFoundError(f"No jobs found for {config.company_name}")


def filter_jobs(jobs: List[ScrapeResult], **_: Any) -> dict[str, List[ScrapeResult]]:
    """
    Return only jobs that match Observer's title and location filters.
    """
    filtered_jobs = list(filter(filter_job, jobs))
    logger.info("Found %s jobs after filtering", len(filtered_jobs))
    return {"jobs": filtered_jobs}
