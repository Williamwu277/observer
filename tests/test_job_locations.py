import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrapers"))

from discord_integration import WebhookType
from models import ScrapeResult, ScrapeStatus, StatusResult
from run_summary import build_run_summary
from scrape import (
    send_discord_notifications,
    store_scrape_result,
    update_scraper_results,
)
class FakeSheetManager:
    def __init__(self, rows):
        self.rows = rows
        self.updates = []

    def read_sheet(self, _range_name):
        return self.rows

    def update_spreadsheet(self, rows, range_name):
        self.updates.append((rows, range_name))


class JobOutputTests(unittest.TestCase):
    def operational_statuses(self, company):
        return [StatusResult(company, "https://example.com", ScrapeStatus.OPERATIONAL, "now", 1, 1)]

    def test_duplicate_urls_merge_unique_locations_in_scrape_order(self):
        results = {}
        locations_by_url = {}
        locations = [
            None,
            " New\nYork ",
            "Seattle",
            "new york",
            "South San Francisco HQ",
        ]

        for location in locations:
            store_scrape_result(
                results,
                locations_by_url,
                ScrapeResult("stripe", "shared", "Software Engineer Intern", location),
            )

        self.assertEqual(list(results), ["shared"])
        self.assertEqual(
            results["shared"].location,
            "New York; Seattle; South San Francisco HQ",
        )

    @patch("scrape.send_discord_batch_update", return_value=True)
    def test_merged_locations_create_one_sheet_row_and_announcement(self, send_batch):
        results = {}
        locations_by_url = {}
        for location in ["New York", "Seattle", "South San Francisco HQ"]:
            store_scrape_result(
                results,
                locations_by_url,
                ScrapeResult("stripe", "shared", "Software Engineer Intern", location),
            )

        manager = FakeSheetManager([])
        update_scraper_results(manager, self.operational_statuses("stripe"), results)
        send_discord_notifications([], results)

        self.assertEqual(len(manager.updates[0][0]), 1)
        self.assertEqual(
            manager.updates[0][0][0][4],
            "New York; Seattle; South San Francisco HQ",
        )
        messages = send_batch.call_args.args[1]
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0]["description"],
            "Software Engineer Intern\n"
            "Location: New York; Seattle; South San Francisco HQ",
        )

    def test_new_rows_and_existing_location_backfills_use_six_columns(self):
        rows = [
            ["old date", "acme", "Existing Intern", "existing", "", "Active"],
            ["old date", "acme", "Known Intern", "known", "Toronto", "Active"],
        ]
        manager = FakeSheetManager(rows)
        results = {
            "existing": ScrapeResult(
                "acme", "existing", "Existing Intern", "  New\n York  ", "now"
            ),
            "known": ScrapeResult("acme", "known", "Known Intern", "   ", "now"),
            "new": ScrapeResult("acme", "new", "New Intern", " Vancouver ", "now"),
        }

        expired = update_scraper_results(manager, self.operational_statuses("acme"), results)

        self.assertEqual(expired, 0)
        self.assertEqual(list(results), ["new"])
        updated_rows, update_range = manager.updates[0]
        self.assertEqual(update_range, "2026!A2:F")
        self.assertEqual(
            updated_rows[0],
            ["now", "acme", "New Intern", "new", "Vancouver", "Active"],
        )
        self.assertEqual(updated_rows[1][4], "New York")
        self.assertEqual(updated_rows[2][4], "Toronto")

    def test_location_only_backfill_is_persisted_without_new_listing(self):
        rows = [["old date", "acme", "Intern", "existing", "", "Active"]]
        manager = FakeSheetManager(rows)
        results = {
            "existing": ScrapeResult(
                "acme", "existing", "Intern", "Seattle", "now"
            )
        }

        update_scraper_results(manager, self.operational_statuses("acme"), results)

        self.assertEqual(results, {})
        self.assertEqual(manager.updates[0][0][0][4], "Seattle")

    def test_expiration_and_unprocessed_rows_still_behave_the_same(self):
        rows = [
            ["date", "acme", "Gone Intern", "gone", "Toronto", "Active"],
            ["date", "other", "Other Intern", "other", "Seattle", "Active"],
        ]
        manager = FakeSheetManager(rows)

        expired = update_scraper_results(manager, self.operational_statuses("acme"), {})

        self.assertEqual(expired, 1)
        self.assertEqual(rows[0][5], "Expired")
        self.assertEqual(rows[1][5], "Active")

    @patch("scrape.send_discord_batch_update", return_value=True)
    def test_discord_announcements_include_location_only_when_present(self, send_batch):
        results = {
            "with": ScrapeResult("acme", "with", "Intern One", " New\nYork "),
            "without": ScrapeResult("acme", "without", "Intern Two", None),
        }

        self.assertEqual(send_discord_notifications([], results), (1, 1))

        webhook_type, messages = send_batch.call_args.args
        self.assertEqual(webhook_type, WebhookType.ANNOUNCEMENTS)
        self.assertEqual(messages[0]["description"], "Intern One\nLocation: New York")
        self.assertEqual(messages[1]["description"], "Intern Two")

    def test_run_summary_does_not_include_location(self):
        listing = ScrapeResult(
            "acme", "https://example.com/job", "Software Intern", "SECRET PLACE"
        )

        summary = build_run_summary([], 1, [listing], 0, 1, 0, 0, True)

        self.assertIn("acme — Software Intern — https://example.com/job", summary)
        self.assertNotIn("SECRET PLACE", summary)


if __name__ == "__main__":
    unittest.main()
