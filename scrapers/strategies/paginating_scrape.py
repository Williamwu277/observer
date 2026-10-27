import logging

from playwright.sync_api import Page, TimeoutError
from dataclasses import dataclass
from typing import List
from random import uniform

from models import BrowserScrapeConfig, ScrapeResult, IncompleteScrapeError


logger = logging.getLogger(__name__)
MAX_PAGES = 20


@dataclass
class PaginatingScrapeConfig(BrowserScrapeConfig):
    """
    Config class to customize simple_scrape for alternate portals.
    next_page_selector must point to a button that is clickable.
    """

    next_page_selector: str


def paginating_scrape(
    config: PaginatingScrapeConfig, page: Page
) -> dict[str, List[ScrapeResult]]:
    """
    Scraping function for portals where there may be multiple pages of jobs.
    """

    jobs_list = []
    seen_pages = set()

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

        page_urls = tuple(sorted(
            job.locator(config.url_selector).first.get_attribute("href") or ""
            for job in current_page_jobs
        ))
        if page_urls and page_urls in seen_pages:
            raise IncompleteScrapeError(
                f"Pagination repeated a page for {config.company_name}"
            )
        seen_pages.add(page_urls)

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

        logger.info(
            "Found %s jobs on page %s", len(current_page_jobs), page_number + 1
        )

        # Ensure the selector already makes sure the button is clickable
        next_page_element = page.locator(config.next_page_selector)
        if next_page_element.count() == 0 or not next_page_element.is_enabled():
            break

        if not current_page_jobs:
            raise IncompleteScrapeError(
                f"Empty page with more jobs available for {config.company_name}"
            )

        if page_number + 1 == MAX_PAGES:
            raise IncompleteScrapeError(
                f"More jobs remain after {MAX_PAGES} pages for {config.company_name}"
            )

        next_page_element.click()

        # Pray the website loaded the next page
        page.wait_for_timeout(uniform(3000, 5000))

    logger.info("Found %s jobs total", len(jobs_list))

    return {"jobs": jobs_list}
