from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Shopify",
    base_url="https://internships.shopify.com",
    jobs_selector="div.hero-component_text:has(a)",
    url_selector="a",
    title_selector="a",
)

strategy = simple_scrape
