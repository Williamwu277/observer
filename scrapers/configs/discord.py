"""
Read Discord's main Greenhouse job board.
"""

from models import GreenhouseScrapeConfig
from strategies.greenhouse import greenhouse_scrape


config = GreenhouseScrapeConfig(
    company_name="discord",
    base_url="https://discord.com/careers",
    api_url="https://api.greenhouse.io/v1/boards/discord/jobs",
)

strategy = greenhouse_scrape
