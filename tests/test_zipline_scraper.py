import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrapers"))

from configs.zipline import JOBS_URL, config, zipline_scrape


class ZiplineScraperTests(unittest.TestCase):
    def test_feed_keeps_existing_urls_and_locations(self):
        page = Mock()
        page.request.get.return_value = Mock(ok=True)
        page.request.get.return_value.json.return_value = {
            "jobs": [
                {
                    "id": 7907191003,
                    "title": "Software Engineer Intern (Spring 2027)",
                    "absolute_url": "https://www.zipline.com/open-roles/7907191003?gh_jid=7907191003",
                    "location": {"name": "South San Francisco, California, USA"},
                }
            ],
            "meta": {"total": 1},
        }

        jobs = zipline_scrape(config, page)["jobs"]

        page.request.get.assert_called_once_with(JOBS_URL)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].company_name, "zipline")
        self.assertEqual(jobs[0].url, "https://www.zipline.com/open-roles/7907191003")
        self.assertEqual(jobs[0].title, "Software Engineer Intern (Spring 2027)")
        self.assertEqual(jobs[0].location, "South San Francisco, California, USA")

    def test_http_failure_does_not_return_an_empty_list(self):
        page = Mock()
        page.request.get.return_value = Mock(ok=False, status=503)

        with self.assertRaisesRegex(RuntimeError, "Zipline job feed returned HTTP 503"):
            zipline_scrape(config, page)


if __name__ == "__main__":
    unittest.main()
