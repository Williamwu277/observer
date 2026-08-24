from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="waymo",
    base_url="https://careers.withwaymo.com/jobs/search?page=1&employment_type_uids%5B%5D=fa4c4a8317c6c87309f488cb0d63aa7c&query=",
    jobs_selector='a[href*="https://careers.withwaymo.com"]',
    url_selector=":scope",
    title_selector=":scope",
    cookies_accept_text='I accept',
    empty_portal_selector="p:has-text('No results found')"
)

strategy = simple_scrape
