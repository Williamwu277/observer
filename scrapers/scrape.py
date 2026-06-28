import logging

from datetime import datetime
from time import sleep, perf_counter
from random import uniform, shuffle, choice
from importlib import import_module
from sys import argv
from typing import List, Dict, Tuple
from playwright.sync_api import Playwright, sync_playwright
from playwright_stealth import Stealth

from const import (
    USER_AGENTS,
    DATA_MAP,
    VIEWPORT_CONFIGURATIONS,
    INTERNSHIP_RANGE,
    STATUS_RANGE,
    STATUS_DATA_MAP,
    STATUS_OPERATIONAL,
    STATUS_QUESTIONABLE,
    STATUS_DOWN,
)
from utils import get_company_directory, trim_logs, attach_network_monitor
from sheet_manager import SheetManager
from discord_integration import send_discord_batch_update
from scraping_framework import scrape_integration
from models import ScrapeResult, StatusResult, NoJobsFoundError


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] (%(levelname)s) %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f"logs/scrape_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        ),
    ],
)

logger = logging.getLogger(__name__)


def run_scrapers(
    playwright: Playwright, scraper_names: List[str]
) -> Tuple[Dict[str, ScrapeResult], List[StatusResult]]:
    """
    Entry point for running the scraping process
    """
    # headless=False and args=["--headless=new"] avoid roblox not loading for some reason
    browser = playwright.chromium.launch(
        headless=False,
        args=["--headless=new"],
    )

    scraped_results = {}
    status_results = []

    for i, name in enumerate(scraper_names):
        context = browser.new_context(
            user_agent=choice(USER_AGENTS),
            viewport=choice(VIEWPORT_CONFIGURATIONS),
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        # Measure the data a residential proxy would transfer for this scrape
        get_transferred_bytes = attach_network_monitor(context.new_cdp_session(page))

        logger.info(f"Now scraping: {name}")

        status = STATUS_OPERATIONAL
        portal_url = ""
        start_time = perf_counter()

        try:
            integration = import_module(f"configs.{name}")
            portal_url = integration.config.base_url
            results = scrape_integration(integration.config, integration.strategy, page)
            for result in results:
                if result.url in scraped_results:
                    logger.warning(f"Duplicate URL found: {result.url}")
                # Resetting name prevents duplicate spreadsheet updates
                result.company_name = name
                result.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                scraped_results[result.url] = result
                logger.info(scraped_results[result.url])
        except NoJobsFoundError:
            logger.warning(f"No jobs found while scraping {name}")
            status = STATUS_QUESTIONABLE
        except Exception:
            logger.error(f"Error scraping {name}", exc_info=True)
            status = STATUS_DOWN

        status_results.append(
            StatusResult(
                company_name=name,
                portal_url=portal_url,
                status=status,
                last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                scrape_time=round(perf_counter() - start_time, 2),
                request_size=round(get_transferred_bytes() / (1024 * 1024), 2),
            )
        )

        context.close()
        logger.info(f"Finished scraping: {name}")

        if i < len(scraper_names) - 1:
            sleep(uniform(2, 10))

    browser.close()
    return scraped_results, status_results


def update_status(
    sheet_manager: SheetManager, status_results: List[StatusResult]
) -> None:
    """
    Write the health of each scraped integration to the Status sheet. Merges with
    the existing rows so that partial runs only update the integrations they scraped.
    """
    if len(status_results) == 0:
        return

    name_column = STATUS_DATA_MAP["Name"]
    existing = sheet_manager.read_sheet(STATUS_RANGE)
    status_by_name = {row[name_column]: row for row in existing if row}

    for result in status_results:
        status_by_name[result.company_name] = [
            result.company_name,
            result.portal_url,
            result.status,
            result.last_updated,
            result.scrape_time,
            result.request_size,
        ]

    # Sort by name so rows stay in a stable order between runs
    status_rows = [status_by_name[name] for name in sorted(status_by_name)]

    logger.info(f"Updating status for {len(status_results)} integrations")
    sheet_manager.update_spreadsheet(status_rows, STATUS_RANGE)


def scrape_internships(company_queue: List[str]):
    """
    Scrape the internships, update the spreadsheet store and send the updates to Discord
    """
    logger.info("Starting scraping process")

    with sync_playwright() as playwright:
        scraped_results, status_results = run_scrapers(playwright, company_queue)

    logger.info("Syncing scrape results to spreadsheet data")

    sheet_manager = SheetManager()
    sheet_manager.start()
    data = sheet_manager.read_sheet(INTERNSHIP_RANGE)

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
            "Active",
        ]
        for url in scraped_results
    ]

    logger.info(f"Found a total of {len(spreadsheet_updates)} new jobs to update!")

    if len(spreadsheet_updates) > 0 or is_dirty:
        sheet_manager.update_spreadsheet(spreadsheet_updates + data, INTERNSHIP_RANGE)

    # Aggregate and update scraper health regardless of whether new jobs were found
    update_status(sheet_manager, status_results)

    if len(spreadsheet_updates) == 0:
        return

    logger.info("Attempting to send Discord updates")

    # Turn the data into a Discord friendly format
    discord_messages = [
        {
            "title": scraped_results[url].company_name,
            "url": scraped_results[url].url,
            "description": scraped_results[url].title,
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
