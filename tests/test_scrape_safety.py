import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import imagehash

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrapers"))

from configs.zipline import config as zipline_config
from const import INTERNSHIP_RANGE, STATUS_RANGE
from models import IncompleteScrapeError, ScrapeResult, ScrapeStatus, StatusResult
from scrape import scrape_internships, update_scraper_results
from scraping_framework import scrape_integration
from strategies.greenhouse import greenhouse_scrape
from strategies.paginating_scrape import PaginatingScrapeConfig, paginating_scrape
from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


class FeedSafetyTests(unittest.TestCase):
    def test_malformed_or_incomplete_feed_is_rejected(self):
        for payload in (
            {"jobs": []},
            {"jobs": {}, "meta": {"total": 0}},
            {"jobs": [{"id": 1}], "meta": {"total": 2}},
        ):
            with self.subTest(payload=payload), self.assertRaises(IncompleteScrapeError):
                greenhouse_scrape(zipline_config, payload)

    def test_verified_empty_feed_succeeds_without_browser_review(self):
        response = Mock(
            ok=True,
            status_code=200,
            content=b'{"jobs": [], "meta": {"total": 0}}',
        )
        response.json.return_value = {"jobs": [], "meta": {"total": 0}}
        resources = Mock()
        resources.get_http_client.return_value.get.return_value = response
        integration = SimpleNamespace(
            config=zipline_config,
            strategy=greenhouse_scrape,
        )

        self.assertEqual(scrape_integration(integration, resources), [])

        resources.browser_page.assert_not_called()
        resources.get_http_client.return_value.get.assert_called_once_with(
            zipline_config.api_url,
            timeout=30,
        )

    def test_failed_api_request_is_not_retried(self):
        response = Mock(ok=False, status_code=503, content=b"")
        resources = Mock()
        resources.get_http_client.return_value.get.return_value = response
        integration = SimpleNamespace(
            config=zipline_config,
            strategy=greenhouse_scrape,
        )

        with self.assertRaisesRegex(RuntimeError, "zipline API returned HTTP 503"):
            scrape_integration(integration, resources)

        resources.get_http_client.return_value.get.assert_called_once_with(
            zipline_config.api_url,
            timeout=30,
        )
        resources.browser_page.assert_not_called()


class StrategySafetyTests(unittest.TestCase):
    def make_page(self):
        page = Mock()
        cards = Mock()
        card = Mock()
        card.locator.return_value.first.get_attribute.return_value = "https://example.com/job"
        card.locator.return_value.first.text_content.return_value = "Software Engineer Intern"
        cards.all.return_value = [card]
        button = Mock()
        button.count.return_value = 1
        button.is_enabled.return_value = True
        page.locator.side_effect = lambda selector: button if selector == "next" else cards
        return page, button

    def test_pagination_limit_does_not_return_a_partial_list(self):
        page, button = self.make_page()
        config = PaginatingScrapeConfig("acme", "https://example.com", "cards", "a", "h3", "next")
        with patch("strategies.paginating_scrape.MAX_PAGES", 1):
            with self.assertRaisesRegex(IncompleteScrapeError, "More jobs remain"):
                paginating_scrape(config, page)
        button.click.assert_not_called()

    def test_failed_page_navigation_is_detected(self):
        page, _ = self.make_page()
        config = PaginatingScrapeConfig("acme", "https://example.com", "cards", "a", "h3", "next")
        with self.assertRaisesRegex(IncompleteScrapeError, "repeated a page"):
            paginating_scrape(config, page)

    def test_last_page_at_limit_is_complete(self):
        page, button = self.make_page()
        button.is_enabled.return_value = False
        config = PaginatingScrapeConfig("acme", "https://example.com", "cards", "a", "h3", "next")
        with patch("strategies.paginating_scrape.MAX_PAGES", 1):
            self.assertEqual(len(paginating_scrape(config, page)["jobs"]), 1)

    def test_load_more_limit_does_not_return_a_partial_list(self):
        page, _ = self.make_page()
        config = SimpleScrapeConfig("acme", "https://example.com", "cards", "a", "h3", more_jobs_selector="next")
        with patch("strategies.simple_scrape.MAX_MORE_JOBS_CLICKS", 1):
            with self.assertRaisesRegex(IncompleteScrapeError, "More jobs remain"):
                simple_scrape(config, page)


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        cleanup = patch("scrape.shutil.rmtree")
        cleanup.start()
        self.addCleanup(cleanup.stop)

    @patch("scrape.send_discord_summary")
    @patch("scrape.send_discord_batch_update", return_value=True)
    @patch("scrape.send_discord_update", return_value=True)
    @patch("scrape.SheetManager")
    @patch("scrape.run_scrapers")
    @patch("scrape.sync_playwright")
    def test_only_trusted_runs_change_jobs_and_announce_but_all_statuses_update(
        self, playwright, run_scrapers, manager_class, send_error, send_jobs, send_summary
    ):
        rows = [
            ["date", "failed", "Old Intern", "https://example.com/failed", "Toronto", "Active"],
            ["date", "empty", "Old Intern", "https://example.com/empty", "Toronto", "Active"],
            ["date", "confident", "Old Intern", "https://example.com/confident", "Toronto", "Active"],
            ["date", "success", "Gone Intern", "https://example.com/gone", "Toronto", "Active"],
            ["date", "success", "Existing Intern", "https://example.com/existing", "Toronto", "Active"],
            ["date", "unqueued", "Old Intern", "https://example.com/unqueued", "Toronto", "Active"],
        ]
        manager = manager_class.return_value
        untouched_status = ["unqueued", "https://example.com", "Operational", "before", 1, 1, "0"]
        manager.read_sheet.side_effect = lambda range_name: (
            [untouched_status] if range_name == STATUS_RANGE else rows
        )
        statuses = [
            StatusResult(name, "https://example.com", status, "now", 1, 1)
            for name, status in (
                ("failed", ScrapeStatus.DOWN),
                ("empty", ScrapeStatus.QUESTIONABLE),
                ("confident", ScrapeStatus.CONFIDENT),
                ("success", ScrapeStatus.OPERATIONAL),
            )
        ]
        statuses[0].error = "Scrape failed"
        run_scrapers.return_value = ({
            "https://example.com/failed": ScrapeResult("failed", "https://example.com/failed", "Old Intern", "Seattle"),
            "https://example.com/partial": ScrapeResult("failed", "https://example.com/partial", "Partial Intern"),
            "https://example.com/untrusted": ScrapeResult("empty", "https://example.com/untrusted", "Untrusted Intern"),
            "https://example.com/existing": ScrapeResult("success", "https://example.com/existing", "Existing Intern", "Seattle"),
            "https://example.com/new": ScrapeResult("success", "https://example.com/new", "New Intern"),
        }, statuses)

        scrape_internships(["failed", "empty", "confident", "success"])

        writes = {call.args[1]: call.args[0] for call in manager.update_spreadsheet.call_args_list}
        written = writes[INTERNSHIP_RANGE]
        self.assertEqual([row[5] for row in rows], ["Active", "Active", "Expired", "Expired", "Active", "Active"])
        self.assertEqual(rows[0][4], "Toronto")
        self.assertEqual(rows[4][4], "Seattle")
        self.assertEqual(len(written), 7)
        self.assertEqual(written[0][3], "https://example.com/new")
        self.assertEqual([message["url"] for message in send_jobs.call_args.args[1]], ["https://example.com/new"])
        errors_by_name = {
            call.args[1][0]["title"]: call.args[1][0]["description"]
            for call in send_error.call_args_list
        }
        self.assertEqual(errors_by_name["failed"], "Scrape failed")
        self.assertIn("empty", errors_by_name)
        status_by_name = {row[0]: row for row in writes[STATUS_RANGE]}
        for result in statuses:
            self.assertEqual(status_by_name[result.company_name][2], result.status.value)
        self.assertEqual(status_by_name["unqueued"], untouched_status)
        summary = send_summary.call_args.args[0]
        self.assertIn("1 new listing added", summary)
        self.assertIn("2 listings marked expired", summary)
        self.assertNotIn("Partial Intern", summary)
        self.assertNotIn("Untrusted Intern", summary)

    def test_untrusted_or_missing_status_cannot_write_jobs(self):
        manager = Mock()
        statuses = [
            StatusResult(name, "https://example.com", status, "now", 1, 1)
            for name, status in (("failed", ScrapeStatus.DOWN), ("empty", ScrapeStatus.QUESTIONABLE))
        ]
        results = {
            name: ScrapeResult(name, name, "Intern")
            for name in ("failed", "empty", "missing")
        }

        self.assertEqual(update_scraper_results(manager, statuses, results), 0)

        self.assertEqual(results, {})
        manager.read_sheet.assert_not_called()
        manager.update_spreadsheet.assert_not_called()

    def test_trusted_empty_runs_expire_existing_jobs(self):
        for status in (ScrapeStatus.OPERATIONAL, ScrapeStatus.CONFIDENT):
            with self.subTest(status=status):
                manager = Mock()
                row = ["date", "acme", "Intern", "old", "Toronto", "Active"]
                manager.read_sheet.return_value = [row]
                statuses = [StatusResult("acme", "https://example.com", status, "now", 1, 1)]

                self.assertEqual(update_scraper_results(manager, statuses, {}), 1)

                self.assertEqual(row[5], "Expired")
                manager.update_spreadsheet.assert_called_once_with([row], INTERNSHIP_RANGE)

    @patch("scrape.Path.exists")
    @patch("scrape.calculate_pHash", return_value=imagehash.hex_to_hash("0000000000000000"))
    @patch("scrape.SheetManager")
    @patch("scrape.run_scrapers")
    @patch("scrape.sync_playwright")
    def test_empty_browser_jobs_use_resolved_screenshot_status(
        self, playwright, run_scrapers, manager_class, calculate_hash, screenshot_exists
    ):
        for previous_hash, has_screenshot, expected_status in (
            ("0", True, ScrapeStatus.CONFIDENT),
            ("0000000000000000", True, ScrapeStatus.CONFIDENT),
            ("ffffffffffffffff", True, ScrapeStatus.DOWN),
            ("0000000000000000", False, ScrapeStatus.QUESTIONABLE),
        ):
            with self.subTest(previous_hash=previous_hash, has_screenshot=has_screenshot):
                manager = manager_class.return_value
                manager.reset_mock()
                row = ["date", "acme", "Intern", "old", "Toronto", "Active"]
                previous = ["acme", "https://example.com", "Confident", "before", 1, 1, previous_hash]
                manager.read_sheet.side_effect = lambda range_name: (
                    [previous] if range_name == STATUS_RANGE else [row]
                )
                statuses = [StatusResult("acme", "https://example.com", ScrapeStatus.QUESTIONABLE, "now", 1, 1)]
                run_scrapers.return_value = ({}, statuses)
                screenshot_exists.return_value = has_screenshot

                scrape_internships(["acme"], debug=True)

                writes = {call.args[1]: call.args[0] for call in manager.update_spreadsheet.call_args_list}
                self.assertEqual(writes[STATUS_RANGE][0][2], expected_status.value)
                if expected_status == ScrapeStatus.CONFIDENT:
                    self.assertEqual(writes[STATUS_RANGE][0][6], "0000000000000000")
                    self.assertEqual(row[5], "Expired")
                    self.assertIn(INTERNSHIP_RANGE, writes)
                else:
                    self.assertEqual(row[5], "Active")
                    self.assertNotIn(INTERNSHIP_RANGE, writes)


if __name__ == "__main__":
    unittest.main()
