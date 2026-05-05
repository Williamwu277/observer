from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Uber",
    base_url="https://www.uber.com/us/en/careers/list/?department=University&location=USA-California-San%20Francisco&location=USA-California-Sunnyvale&location=USA-Washington-Seattle",
    jobs_selector='a[aria-label*="Intern"]',
    url_selector=":scope",
    title_selector=":scope",
    more_jobs_selector="button:has-text('Show more openings')",
    link_augmentation="https://www.uber.com",
)

strategy = simple_scrape
