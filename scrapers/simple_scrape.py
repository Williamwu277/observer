import logging
from utils import filter_title, filter_location
from const import LOCATION_WHITELIST, LOCATION_BLACKLIST
from playwright.sync_api import Page, TimeoutError
from dataclasses import dataclass
from typing import Optional, List, Tuple
from random import uniform


logger = logging.getLogger(__name__)


@dataclass
class SimpleScrapeConfig:
    """
    Config class to customize simple_scrape for alternate portals
    """
    company_name: str
    base_url: str
    jobs_selector: str
    url_selector: str
    title_selector: str
    location_selector: Optional[str] = None       # Only necessary if location can be global
    section_click_name: Optional[str] = None      # If the job list is behind a button
    link_augmentation: Optional[str] = ""         # If the scraped url is relative
    strict_title_filter: Optional[bool] = True    # If True, will filter out internships without software keywords


def simple_scrape(config: SimpleScrapeConfig, page: Page) -> List[Tuple[str, str]]:
    """
    Scraping function for portals you can access the job list through through
    up to one click
    """

    logger.info(f"Navigating to: {config.base_url}")

    # Use referer header to simulate coming from a search engine
    page.goto(config.base_url, referer="https://www.google.com/")
    page.wait_for_timeout(uniform(1000, 3000))

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
    logger.info(f"Found {len(jobs_list)} jobs")

    # Filter the jobs
    for job in jobs_list:
        url = config.link_augmentation + job.locator(config.url_selector).first.get_attribute("href")
        title = job.locator(config.title_selector).first.text_content().strip()

        # Check location if necessary
        if config.location_selector:
            location = job.locator(config.location_selector).first.text_content()
            if not filter_location(LOCATION_WHITELIST, location): continue

        # Check job title
        if not filter_title(title, config.strict_title_filter): continue

        # Double check title for location blacklist
        if filter_location(LOCATION_BLACKLIST, title): continue

        results.append((title, url))
    
    logger.info(f"Found {len(results)} jobs after filtering")
    return results
