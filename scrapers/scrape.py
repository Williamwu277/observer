import logging

from datetime import datetime
from time import sleep
from random import uniform, shuffle, choice
from sys import argv
from typing import List, Dict
from playwright.sync_api import Playwright, sync_playwright
from playwright_stealth import Stealth

from const import USER_AGENTS, DATA_MAP
from utils import get_company_directory, trim_logs
from sheet_manager import SheetManager
from discord_integration import send_discord_batch_update
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


def scrape_internships(company_queue: List[str]):
    """
    Scrape the internships, update the spreadsheet store and send the updates to Discord
    """
    logger.info("Starting scraping process")

    with sync_playwright() as playwright:
        scraped_results = run_scrapers(playwright, company_queue)

    logger.info("Syncing scrape results to spreadsheet data")

    sheet_manager = SheetManager()
    sheet_manager.start()
    data = sheet_manager.read_sheet()

    # Reconcile stored data with scraped data
    is_dirty = False
    for row in data:
        status = row[DATA_MAP["Status"]]
        url = row[DATA_MAP["Url"]]
        company_name = row[DATA_MAP["Company"]]

        if company_name not in company_queue or status == "Expired": 
            continue
        elif url not in scraped_results: 
            # If the job was not found in the most recent scrape, it probably isn't active
            row[DATA_MAP["Status"]] = "Expired"
            is_dirty = True
        else: 
            # Get rid of jobs we've already found
            del scraped_results[url]

    # Convert to spreadsheet data format
    spreadsheet_updates = [
        [
            scraped_results[url].timestamp,
            scraped_results[url].company_name,
            scraped_results[url].title,
            scraped_results[url].url,
            "Active"
        ] 
        for url in scraped_results
    ]

    logger.info(f"Found a total of {len(spreadsheet_updates)} new jobs to update!")

    if len(spreadsheet_updates) > 0: 
        sheet_manager.insert_rows(len(spreadsheet_updates))
    
    if len(spreadsheet_updates) > 0 or is_dirty:
        sheet_manager.update_spreadsheet(spreadsheet_updates + data)

    if len(spreadsheet_updates) == 0: return

    logger.info("Attempting to send Discord updates")

    # Turn the data into a Discord friendly format
    discord_messages = [
        {
            "title": scraped_results[url].company_name,
            "url": scraped_results[url].url,
            "description": scraped_results[url].title
        } 
        for url in scraped_results
    ]

    send_discord_batch_update(discord_messages)

    logger.info("Finished scraping internships!")


def main():
    company_names = argv[1:]
    if len(company_names) == 0:
        company_names = get_company_directory()
        logger.info(f"Found {len(company_names)} companies in directory")
    shuffle(company_names)
    scrape_internships(company_names)
    trim_logs()


if __name__ == "__main__":
    main()
