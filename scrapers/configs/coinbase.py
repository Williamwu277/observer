from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="coinbase",
    base_url="https://www.coinbase.com/en-ca/careers/positions?department=Engineering%2CEngineering%2520-%2520Backend%2CEngineering%2520-%2520Frontend%2CEngineering%2520-%2520Infrastructure%2CEngineering%2520-%2520Managers%2CEngineering%2520-%2520Security&search=intern",
    jobs_selector='div:has(> h2:has-text("Internships")) div:has(> a[href^="/careers/positions/"])',
    url_selector="a",
    title_selector="a > span > p",
    location_selector=":scope > p",
    link_augmentation=lambda url: "https://www.coinbase.com/en-ca" + url,
    empty_portal_selector="h3:has-text('Want to see more opportunities?')"
)

strategy = simple_scrape
