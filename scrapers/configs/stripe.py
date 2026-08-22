from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="stripe",
    base_url="https://stripe.com/jobs/search?query=intern",
    jobs_selector="a[href^='https://stripe.com/jobs/listing/']",
    url_selector=":scope",
    title_selector=":scope",
    location_selector="xpath=../..//span[@class='JobsListings__locationDisplayName']",
)

strategy = simple_scrape
