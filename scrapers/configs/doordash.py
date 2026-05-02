from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Doordash",
    base_url="https://careersatdoordash.com/university-careers/",
    jobs_selector="section[id^='jobs-block'] div.job-item",
    url_selector="div.title-container a",
    title_selector="div.title-container a",
    location_selector="div.location-container div:nth-child(2)",
)

strategy = simple_scrape
