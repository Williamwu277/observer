from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="palantir",
    base_url="https://jobs.lever.co/palantir?commitment=Internship",
    jobs_selector="div.posting",
    url_selector="a.posting-title",
    title_selector="h5[data-qa='posting-name']",
    location_selector="span.location",
)

strategy = simple_scrape
