"""Discord's careers page draws its listings from three Greenhouse boards."""

from models import ScrapeConfig, ScrapeResult
from playwright.sync_api import Page


BOARDS = ("discord", "discordinternational", "internationaleor")


def discord_scrape(config: ScrapeConfig, page: Page) -> dict[str, list[ScrapeResult]]:
    """Read every board used by Discord's careers page before returning jobs."""
    jobs = []
    for board in BOARDS:
        url = f"https://api.greenhouse.io/v1/boards/{board}/jobs"
        response = page.request.get(url)
        if not response.ok:
            raise RuntimeError(f"Discord job board {board} returned HTTP {response.status}")

        for posting in response.json()["jobs"]:
            jobs.append(
                ScrapeResult(
                    company_name=config.company_name,
                    title=posting["title"],
                    url=posting["absolute_url"],
                    location=posting["location"]["name"],
                )
            )

    return {"jobs": jobs}


config = ScrapeConfig(
    company_name="discord",
    base_url="https://discord.com/careers",
    # The framework requires selectors; this strategy reads the page's job feeds.
    jobs_selector=".jobs-list .job-item",
    url_selector=":scope",
    title_selector=".heading-28px",
    location_selector=".paragraph-white-opacity50",
)

strategy = discord_scrape
