import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrapers"))

from configs.discord import BOARDS, config, discord_scrape


class DiscordScraperTests(unittest.TestCase):
    def test_reads_all_careers_boards(self):
        page = Mock()
        responses = []
        for board in BOARDS:
            response = Mock(ok=True)
            response.json.return_value = {
                "jobs": [
                    {
                        "title": f"Software Engineer Intern - {board}",
                        "absolute_url": f"https://job-boards.greenhouse.io/{board}/jobs/123",
                        "location": {"name": "San Francisco, CA"},
                    }
                ]
            }
            responses.append(response)
        page.request.get.side_effect = responses

        jobs = discord_scrape(config, page)["jobs"]

        self.assertEqual(len(jobs), len(BOARDS))
        self.assertEqual([job.company_name for job in jobs], ["discord"] * 3)
        self.assertEqual([job.location for job in jobs], ["San Francisco, CA"] * 3)
        self.assertEqual(
            [call.args[0] for call in page.request.get.call_args_list],
            [f"https://api.greenhouse.io/v1/boards/{board}/jobs" for board in BOARDS],
        )

    def test_failed_board_stops_scrape_instead_of_expiring_its_jobs(self):
        page = Mock()
        first_board = Mock(ok=True)
        first_board.json.return_value = {"jobs": []}
        page.request.get.side_effect = [first_board, Mock(ok=False, status=503)]

        with self.assertRaisesRegex(
            RuntimeError, "Discord job board discordinternational returned HTTP 503"
        ):
            discord_scrape(config, page)


if __name__ == "__main__":
    unittest.main()
