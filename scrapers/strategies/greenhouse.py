import logging

from models import GreenhouseScrapeConfig, IncompleteScrapeError, ScrapeResult


logger = logging.getLogger(__name__)


def greenhouse_scrape(
    config: GreenhouseScrapeConfig, payload: dict, **_: object
) -> dict:
    """
    Validate and convert a complete Greenhouse job feed.
    """
    jobs = payload.get("jobs")
    total = payload.get("meta", {}).get("total")
    if not isinstance(jobs, list) or type(total) is not int or len(jobs) != total:
        raise IncompleteScrapeError("Greenhouse job count does not match meta.total")

    results = []
    for posting in jobs:
        url = posting["absolute_url"]
        if config.link_augmentation:
            url = config.link_augmentation(url)

        results.append(
            ScrapeResult(
                company_name=config.company_name,
                url=url,
                title=posting["title"],
                location=posting.get("location", {}).get("name"),
            )
        )

    logger.info("Found %s jobs", len(results))
    return {"jobs": results}
