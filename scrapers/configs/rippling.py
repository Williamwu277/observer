from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Rippling",
    base_url="https://www.rippling.com/en-CA/careers/open-roles",
    jobs_selector="a[href^='https://ats.rippling.com/rippling/jobs/']",
    url_selector=":scope",
    title_selector=":scope > p",
    location_selector="div > p",
)

strategy = simple_scrape
