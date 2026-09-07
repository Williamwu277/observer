from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="duolingo",
    base_url="https://careers.duolingo.com/?type=Intern#careers",
    jobs_selector='a[href*="/jobs"]',
    url_selector=":scope",
    title_selector=":scope",
    link_augmentation=lambda url: "https://careers.duolingo.com" + url,
    empty_portal_selector="div:has-text('No jobs currently match this selection')"
)

strategy = simple_scrape
