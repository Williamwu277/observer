from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="lyft",
    base_url="https://www.lyft.com/careers/early-talent",
    jobs_selector="a[href*='app.careerpuck.com']",
    url_selector=":scope",
    title_selector="h3",
    empty_portal_selector="span:has-text('Sorry, no jobs were found for that criteria.')"
)

strategy = simple_scrape
