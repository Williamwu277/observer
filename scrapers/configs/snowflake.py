from simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Snowflake",
    base_url="https://careers.snowflake.com/us/en/search-results?keywords=intern",
    jobs_selector="li.jobs-list-item",
    url_selector="span[role='heading'] a",
    title_selector="span[role='heading'] a",
    location_selector="p.job-info",
)

strategy = simple_scrape
