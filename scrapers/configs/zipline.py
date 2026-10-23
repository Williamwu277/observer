"""Read the Greenhouse feed used by Zipline's careers page."""

from playwright.sync_api import Page

from models import ScrapeConfig, ScrapeResult
from strategies.greenhouse import validate_greenhouse_jobs


JOBS_URL = "https://boards-api.greenhouse.io/v1/boards/flyzipline/jobs"


def zipline_scrape(config: ScrapeConfig, page: Page) -> dict:
    response = page.request.get(JOBS_URL)
    if not response.ok:
        raise RuntimeError(f"Zipline job feed returned HTTP {response.status}")

    return {
        "jobs": [
            ScrapeResult(
                company_name=config.company_name,
                # Preserve existing sheet identities; absolute_url adds ?gh_jid=.
                url=f"https://www.zipline.com/open-roles/{posting['id']}",
                title=posting["title"],
                location=posting["location"]["name"],
            )
            for posting in validate_greenhouse_jobs(response.json())
        ],
        "complete": True,
    }


config = ScrapeConfig(
    company_name="zipline",
    base_url="https://www.zipline.com/open-roles?q=intern",
    # Required by ScrapeConfig; this strategy reads the page's job feed.
    jobs_selector="div[data-role-card='true']",
    url_selector="a",
    title_selector="h3",
    location_selector="div > p:nth-child(2)",
)

strategy = zipline_scrape
