import logging

from playwright.sync_api import Page, TimeoutError
from dataclasses import dataclass
from typing import List
from random import uniform

from models import ScrapeConfig, ScrapeResult, NoJobsFoundError


logger = logging.getLogger(__name__)
MAX_PAGES = 5


@dataclass
class PaginatingScrapeConfig(ScrapeConfig):
    """
    Config class to customize simple_scrape for alternate portals
    next_page_selector must point to a button that is clickable
    """

    next_page_selector: str


def paginating_scrape(
    config: PaginatingScrapeConfig, page: Page
) -> dict[str, List[ScrapeResult]]:
    """
    Scraping function for portals where there may be multiple pages of jobs
    """

    jobs_list = []

    for page_number in range(MAX_PAGES):
        current_page_jobs = []

        # Grab all the jobs
        try:
            page.locator(config.jobs_selector).first.wait_for(
                state="attached", timeout=5000
            )
            current_page_jobs = page.locator(config.jobs_selector).all()
        except TimeoutError:
            if page_number > 0:
                raise Exception(
                    f"No jobs found on page {page_number + 1} for {config.company_name}"
                )

        # Grab the information from each job
        for job in current_page_jobs:
            url = job.locator(config.url_selector).first.get_attribute("href")
            if config.link_augmentation:
                url = config.link_augmentation(url)
            title = job.locator(config.title_selector).first.text_content().strip()

            # Check location if necessary
            location = None
            if config.location_selector:
                location = job.locator(config.location_selector).first.text_content()

            jobs_list.append(
                ScrapeResult(
                    company_name=config.company_name,
                    url=url,
                    title=title,
                    location=location,
                )
            )

        logger.info(f"Found {len(current_page_jobs)} jobs on page {page_number + 1}")

        # Ensure the selector already makes sure the button is clickable
        next_page_element = page.locator(config.next_page_selector)
        if next_page_element.count() == 0 or not next_page_element.is_enabled():
            break

        next_page_element.click()

        # Pray the website loaded the next page
        page.wait_for_timeout(uniform(3000, 5000))

    logger.info(f"Found {len(jobs_list)} jobs total")

    if len(jobs_list) == 0:
        raise NoJobsFoundError(f"No jobs found for {config.company_name}")

    return {"jobs": jobs_list}
