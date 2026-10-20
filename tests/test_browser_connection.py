import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrapers"))

from scrape import start_browser


class BrowserConnectionTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_local_launch_preserves_full_chromium_workaround(self):
        playwright = Mock()

        browser = start_browser(playwright)

        self.assertIs(browser, playwright.chromium.launch.return_value)
        playwright.chromium.launch.assert_called_once_with(
            headless=False, args=["--headless=new"]
        )
        playwright.chromium.connect.assert_not_called()

    @patch.dict(os.environ, {"PLAYWRIGHT_SERVER_URL": "ws://browser:3000/"})
    def test_remote_connection_requests_full_chromium(self):
        playwright = Mock()

        browser = start_browser(playwright)

        self.assertIs(browser, playwright.chromium.connect.return_value)
        args, kwargs = playwright.chromium.connect.call_args
        self.assertEqual(args, ("ws://browser:3000/",))
        self.assertEqual(kwargs["timeout"], 30_000)
        self.assertEqual(
            json.loads(kwargs["headers"]["x-playwright-launch-options"]),
            {"channel": "chromium", "headless": True},
        )
        playwright.chromium.launch.assert_not_called()

    @patch.dict(os.environ, {"PLAYWRIGHT_SERVER_URL": "ws://browser:3000/"})
    def test_connection_failure_does_not_silently_launch_locally(self):
        playwright = Mock()
        playwright.chromium.connect.side_effect = RuntimeError("Server unavailable")

        with self.assertRaisesRegex(RuntimeError, "Server unavailable"):
            start_browser(playwright)

        playwright.chromium.launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
