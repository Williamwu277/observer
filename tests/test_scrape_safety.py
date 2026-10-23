import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrapers"))

from configs.zipline import config as zipline_config
from models import IncompleteScrapeError, ScrapeResult, ScrapeStatus, StatusResult
from scrape import scrape_internships
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
    @patch("scrape.send_discord_summary")
    @patch("scrape.send_discord_notifications", return_value=(0, 0))
    @patch("scrape.update_scraper_status")
    @patch("scrape.SheetManager")
    @patch("scrape.run_scrapers")
    @patch("scrape.sync_playwright")
    def test_all_queued_companies_reconcile_regardless_of_status(
        self, playwright, run_scrapers, manager_class, update_status, send_jobs, send_summary
    ):
        rows = [
            ["date", "failed", "Old Intern", "https://example.com/failed", "Toronto", "Active"],
            ["date", "empty", "Old Intern", "https://example.com/empty", "Toronto", "Active"],
            ["date", "confident", "Old Intern", "https://example.com/confident", "Toronto", "Active"],
            ["date", "success", "Gone Intern", "https://example.com/gone", "Toronto", "Active"],
            ["date", "unqueued", "Old Intern", "https://example.com/unqueued", "Toronto", "Active"],
        ]
        manager = manager_class.return_value
        manager.read_sheet.return_value = rows
        statuses = [
            StatusResult(name, "https://example.com", status, "now", 1, 1)
            for name, status in (
                ("failed", ScrapeStatus.DOWN),
                ("empty", ScrapeStatus.QUESTIONABLE),
                ("confident", ScrapeStatus.CONFIDENT),
                ("success", ScrapeStatus.OPERATIONAL),
            )
        ]
        run_scrapers.return_value = ({
            "https://example.com/partial": ScrapeResult("failed", "https://example.com/partial", "Partial Intern"),
            "https://example.com/new": ScrapeResult("success", "https://example.com/new", "New Intern"),
        }, statuses)

        scrape_internships(["failed", "empty", "confident", "success"])

        written = manager.update_spreadsheet.call_args.args[0]
        self.assertEqual([row[5] for row in rows], ["Expired"] * 4 + ["Active"])
        self.assertEqual(len(written), 7)
        expected_urls = ["https://example.com/partial", "https://example.com/new"]
        self.assertEqual([row[3] for row in written[:2]], expected_urls)
        self.assertEqual(list(send_jobs.call_args.args[1]), expected_urls)
        update_status.assert_called_once_with(manager, statuses)


if __name__ == "__main__":
    unittest.main()
