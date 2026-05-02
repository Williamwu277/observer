import logging

from playwright.sync_api import Page, TimeoutError
from dataclasses import dataclass
from typing import Optional, List

from models import ScrapeConfig, ScrapeResult


logger = logging.getLogger(__name__)


@dataclass
class SimpleScrapeConfig(ScrapeConfig):
    """
    Config class to customize simple_scrape for alternate portals
    """
    jobs_selector: str
    url_selector: str
    title_selector: str
    location_selector: Optional[str] = None       # Only necessary if location can be global
    section_click_name: Optional[str] = None      # If the job list is behind a button
    link_augmentation: Optional[str] = ""         # If the scraped url is relative


def simple_scrape(config: SimpleScrapeConfig, page: Page) -> dict[str, List[ScrapeResult]]:
    """
    Scraping function for portals you can access the job list through
    up to one click
    """

    # Click on proper section if necessary e.g. Ramp
    if config.section_click_name:
        logger.info(f"Clicking on section: {config.section_click_name}")
        page.get_by_role("button", name=config.section_click_name).click()

    # Grab all the jobs
    try:
        page.locator(config.jobs_selector).first.wait_for(state="attached", timeout=5000)
        jobs_list = page.locator(config.jobs_selector).all()
    except TimeoutError:
        raise Exception(f"No jobs found for {config.company_name}. Double check the jobs selector and url selector.")

    results = []

    # Grab the information from each job
    for job in jobs_list:
        url = config.link_augmentation + job.locator(config.url_selector).first.get_attribute("href")
        title = job.locator(config.title_selector).first.text_content().strip()

        # Check location if necessary
        location = None
        if config.location_selector:
            location = job.locator(config.location_selector).first.text_content()

        results.append(ScrapeResult(company_name=config.company_name, url=url, title=title, location=location))
    
    logger.info(f"Found {len(results)} jobs")

    return {"jobs": results}
