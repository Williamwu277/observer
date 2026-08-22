import logging
import traceback
import shutil
import imagehash

from datetime import datetime
from time import sleep, perf_counter
from random import uniform, shuffle, choice
from importlib import import_module
from pathlib import Path
from sys import argv
from typing import List, Dict, Tuple
from playwright.sync_api import Playwright, sync_playwright
from playwright_stealth import Stealth

from const import (
    USER_AGENTS,
    DATA_MAP,
    VIEWPORT,
    INTERNSHIP_RANGE,
    STATUS_RANGE,
    STATUS_DATA_MAP,
    P_HASH_THRESHOLD,
)
from utils import (
    get_company_directory,
    trim_logs,
    attach_network_monitor,
    calculate_pHash,
)
from sheet_manager import SheetManager
from discord_integration import (
    WebhookType,
    send_discord_batch_update,
    send_discord_update,
    MAX_EMBED_DESCRIPTION_LENGTH,
)
from scraping_framework import scrape_integration
from models import NoJobsFoundError, ScrapeResult, ScrapeStatus, StatusResult


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
    Entry point for starting the scraping process
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
            viewport=VIEWPORT,
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        # Measure the data a residential proxy would transfer for this scrape
        get_transferred_bytes = attach_network_monitor(context.new_cdp_session(page))

        logger.info(f"Now scraping: {name}")

        status = ScrapeStatus.OPERATIONAL
        portal_url = ""
        error = None
        start_time = perf_counter()

        try:
            integration = import_module(f"configs.{name}")
            portal_url = integration.config.base_url
            results = scrape_integration(integration.config, integration.strategy, page)
            for result in results:
                if result.url in scraped_results:
                    logger.warning(f"Duplicate URL found: {result.url}")
                result.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                scraped_results[result.url] = result
                logger.info(scraped_results[result.url])

        except NoJobsFoundError:
            logger.warning(f"No jobs found while scraping {name}")
            status = ScrapeStatus.QUESTIONABLE

        except Exception:
            logger.error(f"Error scraping {name}", exc_info=True)
            status = ScrapeStatus.DOWN
            error = traceback.format_exc()

        status_results.append(
            StatusResult(
                company_name=name,
                portal_url=portal_url,
                status=status,
                last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                scrape_time=round(perf_counter() - start_time, 2),
                request_size=round(get_transferred_bytes() / (1024 * 1024), 2),
                error=error,
            )
        )

        context.close()
        logger.info(f"Finished scraping: {name}")

        if i < len(scraper_names) - 1:
            sleep(uniform(2, 10))

    browser.close()
    return scraped_results, status_results


def update_scraper_status(
    sheet_manager: SheetManager, status_results: List[StatusResult]
) -> None:
    """
    Write the health of each scraped integration to the Status sheet. Merges with
    the existing rows so that partial runs only update the integrations they scraped.
    """
    if len(status_results) == 0:
        return

    logger.info("Syncing scrape status results to spreadsheet")

    name_column = STATUS_DATA_MAP["Name"]
    existing_data = sheet_manager.read_sheet(STATUS_RANGE)
    status_by_name = {row[name_column]: row for row in existing_data if row}

    for result in status_results:
        existing_row = status_by_name.get(result.company_name)
        previous_status = existing_row[STATUS_DATA_MAP["Status"]] if existing_row else None
        previous_pHash = existing_row[STATUS_DATA_MAP["pHash"]] if existing_row else "0"
        screenshot_path = Path(f"tmp/{result.company_name}.png")

        if result.status != ScrapeStatus.QUESTIONABLE:
            """
            If new result is OPERATIONAL or DOWN, we don't need to do anything further
            """
            if (
                result.status == ScrapeStatus.DOWN
                and previous_status == ScrapeStatus.DOWN.value
            ):
                # If the scraper is newly down, we notify the user
                # Otherwise, we don't need to
                result.error = None

        elif previous_status in (
            ScrapeStatus.DOWN.value,
            ScrapeStatus.QUESTIONABLE.value,
        ):
            """
            Scraper is QUESTIONABLE and it was previously DOWN (pHash differed too much) or QUESTIONABLE
            Propagate the previous status forwards
            """
            result.status = ScrapeStatus(previous_status)

        elif (
            previous_status == ScrapeStatus.CONFIDENT.value
            and screenshot_path.exists()
        ):
            """
            Scraper is QUESTIONABLE and it was previously CONFIDENT (user looked at the portal and was confident it still worked)
            Calculate the pHash and compare it with the old one
            """
            logger.info("Calculating pHash to check portal changes")
            new_hash = calculate_pHash(str(screenshot_path))
            if previous_pHash == "0":
                # A human just marked this Confident: capture the baseline.
                result.status = ScrapeStatus.CONFIDENT
                result.pHash = str(new_hash)
            elif imagehash.hex_to_hash(previous_pHash) - new_hash <= P_HASH_THRESHOLD:
                result.status = ScrapeStatus.CONFIDENT
                result.pHash = previous_pHash
            else:
                # Portal changed materially: drop trust, reset for re-verify, notify.
                result.status = ScrapeStatus.DOWN
                result.error = "Warning: the empty portal changed beyond the pHash threshold. Please re-verify and mark it Confident, or fix the scraper."

        elif previous_status == ScrapeStatus.CONFIDENT.value:
            """
            Scraper is QUESTIONABLE and previously CONFIDENT but we don't have a screenshot of it (not set up yet)
            Set as QUESTIONABLE
            """
            result.status = ScrapeStatus.QUESTIONABLE
            result.pHash = previous_pHash
            result.error = "Warning: the scraper found 0 jobs and no empty portal selector was set. Please verify the portal and remedy this."
            
        else:
            """
            There was no previous status. This scraper is new
            """
            result.error = "Warning: scraper is now finding 0 jobs. Please verify the portal and mark it Confident."

        status_by_name[result.company_name] = [
            result.company_name,
            result.portal_url,
            result.status.value,
            result.last_updated,
            result.scrape_time,
            result.request_size,
            result.pHash,
        ]

    shutil.rmtree("tmp", ignore_errors=True)

    status_rows = [status_by_name[name] for name in sorted(status_by_name)]

    logger.info(f"Updating status for {len(status_results)} integration(s)")
    sheet_manager.update_spreadsheet(status_rows, STATUS_RANGE)


def update_scraper_results(
    sheet_manager: SheetManager, company_queue: List[str], scraped_results: Dict[ScrapeResult]
) -> None:
    """
    Write the results of the scraping run to the spreadsheet
    Ensures that the data is consistent
    """
    logger.info("Syncing scrape results to spreadsheet")

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


def send_discord_notifications(status_results: List[StatusResult], scraped_results: Dict[ScrapeResult]):
    """
    Sends all the discord notifications including both error and results found
    """
    # Send scraper errors to the discord error webhook. One at a time to honour embed length limits
    error_messages = [
        {
            "title": status_result.company_name,
            "url": status_result.portal_url,
            "description": status_result.error[-MAX_EMBED_DESCRIPTION_LENGTH:],
        }
        for status_result in status_results
        if status_result.error
    ]

    if len(error_messages) > 0:
        logger.info("Attempting to send scraper error reports to Discord")

        for message in error_messages:
            send_discord_update(WebhookType.ERRORS, [message])

    # update_scraper_results should have already purged redundant scraped_results
    if len(scraped_results) == 0:
        return

    logger.info("Attempting to send internship job announcements on Discord")

    # Turn the data into a Discord friendly format
    discord_messages = [
        {
            "title": scraped_results[url].company_name,
            "url": scraped_results[url].url,
            "description": scraped_results[url].title,
        }
        for url in scraped_results
    ]

    send_discord_batch_update(WebhookType.ANNOUNCEMENTS, discord_messages)


def scrape_internships(company_queue: List[str], debug=False):
    """
    Scrape the internships, update the spreadsheet store and send the updates to Discord
    """
    logger.info("Starting scraping process")

    with sync_playwright() as playwright:
        scraped_results, status_results = run_scrapers(playwright, company_queue)

    sheet_manager = SheetManager()
    sheet_manager.start()

    # Update scraped results on the spreadsheet as well as if the entries are still valid
    update_scraper_results(sheet_manager, company_queue, scraped_results)

    # Aggregate and update scraper health regardless of whether new jobs were found
    update_scraper_status(sheet_manager, status_results)

    if not debug:
        # Send discord notifications
        send_discord_notifications(status_results, scraped_results)

    logger.info("Finished scraping internships!")


def main():
    debug_mode = False
    company_names = argv[1:]
    if '-T' in company_names:
        company_names.remove('-T')
        debug_mode = True
    if len(company_names) == 0:
        company_names = get_company_directory()
        logger.info(f"Found {len(company_names)} companies in directory")
    shuffle(company_names)
    scrape_internships(company_names, debug_mode)
    trim_logs()


if __name__ == "__main__":
    main()
