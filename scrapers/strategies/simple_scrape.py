import logging

from playwright.sync_api import Page, TimeoutError
from dataclasses import dataclass, field
from typing import Optional, List
from random import uniform

from models import ScrapeConfig, ScrapeResult, NoJobsFoundError


logger = logging.getLogger(__name__)
MAX_MORE_JOBS_CLICKS = 10


@dataclass
class SimpleScrapeConfig(ScrapeConfig):
    """
    Config class to customize simple_scrape for alternate portals
    """

    # If the job list is behind a button
    section_click_name: Optional[str] = field(default=None, kw_only=True)
    # If not all jobs are shown at once. Not pagination
    more_jobs_selector: Optional[str] = field(default=None, kw_only=True)


def simple_scrape(
    config: SimpleScrapeConfig, page: Page
) -> dict[str, List[ScrapeResult]]:
    """
    Scraping function for portals you can access the job list through
    up to one click
    """

    # Click on proper section if necessary e.g. Ramp
    if config.section_click_name:
        logger.info(f"Clicking on section: {config.section_click_name}")
        page.get_by_role("button", name=config.section_click_name).click()

    # If not all jobs are shown at once, repeatedly click on more
    if config.more_jobs_selector:
        more_jobs_element = page.locator(config.more_jobs_selector)
        for page_number in range(MAX_MORE_JOBS_CLICKS):
            if more_jobs_element.count() == 0 or not more_jobs_element.is_enabled():
                break
            logger.info(f"Clicking on more jobs button {page_number + 1}")
            more_jobs_element.click()
            page.wait_for_timeout(uniform(3000, 5000))

    # Grab all the jobs
    try:
        page.locator(config.jobs_selector).first.wait_for(
            state="attached", timeout=5000
        )
        jobs_list = page.locator(config.jobs_selector).all()
    except TimeoutError:
        raise NoJobsFoundError(
            f"No jobs found for {config.company_name}. Double check the jobs selector and url selector."
        )

    results = []

    # Grab the information from each job
    for job in jobs_list:
        url = job.locator(config.url_selector).first.get_attribute("href")
        if config.link_augmentation and not url.startswith("https"):
            url = config.link_augmentation(url)
        title = job.locator(config.title_selector).first.text_content().strip()

        # Check location if necessary
        location = None
        if config.location_selector:
            location = job.locator(config.location_selector).first.text_content()

        results.append(
            ScrapeResult(
                company_name=config.company_name,
                url=url,
                title=title,
                location=location,
            )
        )

    logger.info(f"Found {len(results)} jobs")

    return {"jobs": results}
