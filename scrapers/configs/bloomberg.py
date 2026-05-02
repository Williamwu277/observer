from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Bloomberg",
    base_url="https://bloomberg.avature.net/careers/SearchJobs/?1686=%5B55479%5D&1686_format=2312&listFilterMode=1&jobRecordsPerPage=12&",
    jobs_selector="article",
    url_selector="h3 a",
    title_selector="h3",
    location_selector="span",
)

strategy = simple_scrape
