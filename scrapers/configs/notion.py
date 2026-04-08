from simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Notion",
    base_url="https://www.notion.com/careers",
    jobs_selector="section[aria-labelledby='open-positions-university'] a",
    url_selector=":scope",
    title_selector="div:nth-child(1)",
    location_selector="div:nth-child(2)",
)

strategy = simple_scrape
