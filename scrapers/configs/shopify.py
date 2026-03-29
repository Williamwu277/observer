from simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Shopify",
    base_url="https://internships.shopify.com",
    jobs_selector="div.hero-component_text:has(a)",
    url_selector="a",
    title_selector=":scope > p > strong:nth-of-type(2)",
    strict_title_filter=False
)

strategy = simple_scrape
