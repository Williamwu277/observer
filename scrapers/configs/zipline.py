"""
Read the Greenhouse feed used by Zipline's careers page.
"""

from models import GreenhouseScrapeConfig
from strategies.greenhouse import greenhouse_scrape


config = GreenhouseScrapeConfig(
    company_name="zipline",
    base_url="https://www.zipline.com/open-roles?q=intern",
    api_url="https://boards-api.greenhouse.io/v1/boards/flyzipline/jobs",
    link_augmentation=lambda url: url.split("?", maxsplit=1)[0],
)

strategy = greenhouse_scrape
