from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Notion",
    base_url="https://www.notion.com/careers?department=earlycareer",
    jobs_selector="section[aria-labelledby='open-positions-earlycareer'] a",
    url_selector=":scope",
    title_selector="span > span:nth-child(1)",
    location_selector="span > span:nth-child(2)",
)

strategy = simple_scrape
