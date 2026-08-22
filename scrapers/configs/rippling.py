from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="rippling",
    base_url="https://www.rippling.com/en-CA/careers/open-roles?search=intern&department=Engineering",
    jobs_selector="a[href^='https://ats.rippling.com/rippling/jobs/']",
    url_selector=":scope",
    title_selector=":scope > div:nth-child(1) > span:nth-child(1)",
    location_selector=":scope > div:nth-child(1) > div",
)

strategy = simple_scrape
