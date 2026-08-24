from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="zoox",
    base_url="https://zoox.com/careers?q=intern",
    jobs_selector='a[href*="https://jobs.lever.co/zoox/"]',
    url_selector=":scope",
    title_selector="h3",
    section_click_name="Explore All Jobs",
    more_jobs_selector='div[class*="JobSearch_controls"] button',
    empty_portal_selector="h3:has-text('Uh oh! No luck with jobs that match your search!')"
)

strategy = simple_scrape
