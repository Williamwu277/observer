import logging

from datetime import datetime
from time import sleep
from random import uniform, shuffle, choice
from sys import argv
from typing import List, Dict
from playwright.sync_api import Playwright, sync_playwright
from playwright_stealth import Stealth

from const import USER_AGENTS
from utils import get_company_directory, trim_logs
from sheet_manager import update_results
from scraping_framework import scrape_integration
from models import ScrapeResult


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] (%(levelname)s) %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/scrape_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    ]
)

logger = logging.getLogger(__name__)


def run_scrapers(playwright: Playwright, scraper_names: List[str]) -> Dict[str, ScrapeResult]:
    """
    Entry point for running the scraping process
    """
    # headless=False and args=["--headless=new"] avoid roblox not loading for some reason
    browser = playwright.chromium.launch(
        headless=False,
        args=["--headless=new"],
    )

    scraped_results = {}

    for i, name in enumerate(scraper_names):  
        context = browser.new_context(user_agent=choice(USER_AGENTS))
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        logger.info(f"Now scraping: {name}")

        try:
            results = scrape_integration(name, page)
            for result in results:
                if result.url in scraped_results: logger.warning(f"Duplicate URL found: {result.url}")
                # Resetting name prevents duplicate spreadsheet updates
                result.company_name = name
                result.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                scraped_results[result.url] = result
                logger.info(scraped_results[result.url])
        except Exception:
            logger.error(f"Error scraping {name}", exc_info=True)

        context.close()
        logger.info(f"Finished scraping: {name}")

        if i < len(scraper_names) - 1: sleep(uniform(2, 10))

    browser.close()
    return scraped_results


if __name__ == "__main__":
    with sync_playwright() as playwright:
        if len(argv) == 1:
            company_names = get_company_directory()
            logger.info(f"Found {len(company_names)} companies in directory")
            shuffle(company_names)
            scraped_results = run_scrapers(playwright, company_names)
            if len(scraped_results) > 0: update_results(company_names, scraped_results)
        else:
            scraped_results = run_scrapers(playwright, argv[1:])
            if len(scraped_results) > 0: update_results(argv[1:], scraped_results)
    trim_logs()
