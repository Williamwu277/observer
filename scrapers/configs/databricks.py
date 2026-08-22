from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="databricks",
    base_url="https://www.databricks.com/company/careers/open-positions?department=University%20Recruiting&location=USCA",
    jobs_selector="div#jobWrap a",
    url_selector=":scope",
    title_selector="span:nth-child(1)",
    location_selector="span:nth-child(2)",
    link_augmentation=lambda url: "https://www.databricks.com" + url
)

strategy = simple_scrape
