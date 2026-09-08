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
    INTERNSHIP_SHEET,
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
    send_discord_summary,
    send_discord_update,
    MAX_EMBED_DESCRIPTION_LENGTH,
)
from scraping_framework import scrape_integration
from models import NoJobsFoundError, ScrapeResult, ScrapeStatus, StatusResult
from run_summary import build_run_summary


logger = logging.getLogger(__name__)


def normalize_location(location: str | None) -> str:
    """Normalize scraped location text for user-facing outputs."""
    return " ".join((location or "").split())


def configure_logging() -> None:
    """Configure console and file logging for a scraper run."""
    log_directory = Path("logs")
    log_directory.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] (%(levelname)s) %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                log_directory / f"scrape_{datetime.now():%Y-%m-%d_%H-%M-%S}.log"
            ),
        ],
    )


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

        logger.info("Now scraping: %s", name)

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
                    logger.warning("Duplicate URL found: %s", result.url)
                result.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                scraped_results[result.url] = result
                logger.info(scraped_results[result.url])

        except NoJobsFoundError:
            logger.warning("No jobs found while scraping %s", name)
            status = ScrapeStatus.QUESTIONABLE

        except Exception:
            logger.error("Error scraping %s", name, exc_info=True)
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
        logger.info("Finished scraping: %s", name)

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

    logger.info("Updating status for %s integration(s)", len(status_results))
    sheet_manager.update_spreadsheet(status_rows, STATUS_RANGE)


def update_scraper_results(
    sheet_manager: SheetManager,
    company_queue: List[str],
    scraped_results: Dict[str, ScrapeResult],
) -> int:
    """
    Write the results of the scraping run to the spreadsheet
    Ensures that the data is consistent and returns the number of listings expired.
    """
    logger.info("Syncing scrape results to spreadsheet")

    sheet_manager.ensure_job_location_column(INTERNSHIP_SHEET)
    data = sheet_manager.read_sheet(INTERNSHIP_RANGE)

    # Reconcile stored data with scraped data
    expired_listings = 0
    updated_locations = 0
    for row in data:
        status = row[DATA_MAP["Status"]]
        url = row[DATA_MAP["Url"]]
        company_name = row[DATA_MAP["Company"]]

        if company_name not in company_queue or status == "Expired":
            continue

        elif url not in scraped_results:
            # If the job was not found in the most recent scrape, it probably isn't active
            row[DATA_MAP["Status"]] = "Expired"
            expired_listings += 1

        else:
            location = normalize_location(scraped_results[url].location)
            if location and row[DATA_MAP["Location"]] != location:
                row[DATA_MAP["Location"]] = location
                updated_locations += 1
            # Get rid of jobs we've already found
            del scraped_results[url]

    # Convert to spreadsheet data format
    spreadsheet_updates = [
        [
            scraped_results[url].timestamp,
            scraped_results[url].company_name,
            scraped_results[url].title,
            scraped_results[url].url,
            normalize_location(scraped_results[url].location),
            "Active",
        ]
        for url in scraped_results
    ]

    logger.info(
        "Found a total of %s new jobs to update!", len(spreadsheet_updates)
    )
    logger.info("Updated locations for %s existing jobs", updated_locations)

    if len(spreadsheet_updates) > 0 or expired_listings > 0 or updated_locations > 0:
        sheet_manager.update_spreadsheet(spreadsheet_updates + data, INTERNSHIP_RANGE)

    return expired_listings


def send_discord_notifications(
    status_results: List[StatusResult], scraped_results: Dict[str, ScrapeResult]
) -> Tuple[int, int]:
    """
    Sends all Discord notifications and returns attempted and successful group counts.
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

    attempts = 0
    successes = 0

    if len(error_messages) > 0:
        logger.info("Attempting to send scraper error reports to Discord")

        for message in error_messages:
            attempts += 1
            if send_discord_update(WebhookType.ERRORS, [message]):
                successes += 1

    # update_scraper_results should have already purged redundant scraped_results
    if len(scraped_results) == 0:
        return attempts, successes

    logger.info("Attempting to send internship job announcements on Discord")

    # Turn the data into a Discord friendly format
    discord_messages = []
    for result in scraped_results.values():
        description = result.title
        location = normalize_location(result.location)
        if location:
            description += f"\nLocation: {location}"
        discord_messages.append(
            {
                "title": result.company_name,
                "url": result.url,
                "description": description[:MAX_EMBED_DESCRIPTION_LENGTH],
            }
        )

    attempts += 1
    if send_discord_batch_update(WebhookType.ANNOUNCEMENTS, discord_messages):
        successes += 1
    return attempts, successes


def scrape_internships(company_queue: List[str], debug=False):
    """
    Scrape the internships, update the spreadsheet store and send the updates to Discord
    """
    run_start_time = perf_counter()
    logger.info("Starting scraping process")

    with sync_playwright() as playwright:
        scraped_results, status_results = run_scrapers(playwright, company_queue)

    total_listings = len(scraped_results)
    sheet_manager = SheetManager()
    sheet_manager.start()

    # Update scraped results on the spreadsheet as well as if the entries are still valid
    expired_listings = update_scraper_results(
        sheet_manager, company_queue, scraped_results
    )

    # Aggregate and update scraper health regardless of whether new jobs were found
    update_scraper_status(sheet_manager, status_results)

    notification_attempts = 0
    notification_successes = 0
    if not debug:
        # Send discord notifications
        notification_attempts, notification_successes = send_discord_notifications(
            status_results, scraped_results
        )

    summary = build_run_summary(
        status_results=status_results,
        total_listings=total_listings,
        new_listings=list(scraped_results.values()),
        expired_listings=expired_listings,
        elapsed_seconds=perf_counter() - run_start_time,
        notification_attempts=notification_attempts,
        notification_successes=notification_successes,
        notifications_skipped=debug,
    )
    logger.info("Scrape run summary:\n%s", summary)

    if not debug:
        summary_sent = send_discord_summary(summary)
        if summary_sent:
            logger.info("Run summary sent to Discord")


def main():
    configure_logging()

    debug_mode = False
    company_names = argv[1:]
    if '-T' in company_names:
        company_names.remove('-T')
        debug_mode = True
    if len(company_names) == 0:
        company_names = get_company_directory()
        logger.info("Found %s companies in directory", len(company_names))
    shuffle(company_names)
    scrape_internships(company_names, debug_mode)
    trim_logs()


if __name__ == "__main__":
    main()
