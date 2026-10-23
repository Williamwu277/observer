import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrapers"))

from configs.zipline import config, strategy


class ZiplineScraperTests(unittest.TestCase):
    def test_feed_keeps_existing_canonical_url(self):
        payload = {
            "jobs": [
                {
                    "title": "Software Engineer Intern (Spring 2027)",
                    "absolute_url": "https://www.zipline.com/open-roles/7907191003?gh_jid=7907191003",
                    "location": {"name": "South San Francisco, California, USA"},
                }
            ],
            "meta": {"total": 1},
        }

        jobs = strategy(config, payload)["jobs"]

        self.assertEqual(jobs[0].url, "https://www.zipline.com/open-roles/7907191003")

if __name__ == "__main__":
    unittest.main()
