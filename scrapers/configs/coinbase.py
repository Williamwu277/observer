from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Coinbase",
    base_url="https://www.coinbase.com/en-ca/careers/positions?",
    jobs_selector='div:has(> h2:has-text("Internships")) div:has(> a[href^="/careers/positions/"])',
    url_selector="a",
    title_selector="a > span > p",
    location_selector=":scope > p",
    link_augmentation="https://www.coinbase.com/en-ca"
)

strategy = simple_scrape
