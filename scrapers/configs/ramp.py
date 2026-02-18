from simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Ramp",
    base_url="https://ramp.com/careers",
    jobs_selector="section#jobs div[data-state] a",
    url_selector=":scope",
    title_selector=":scope",
    section_click_name="Emerging Talent",
)

strategy = simple_scrape
