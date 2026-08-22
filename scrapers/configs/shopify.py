from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="shopify",
    base_url="https://internships.shopify.com",
    jobs_selector="div.hero-component_text:has(a:not([href*='notification']))",
    url_selector="a",
    title_selector="a",
)

strategy = simple_scrape
