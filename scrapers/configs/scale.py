from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="scale",
    base_url="https://scale.com/careers",
    jobs_selector="div#department-university a",
    url_selector=":scope",
    title_selector="> span",
    location_selector="> div span",
    link_augmentation=lambda url: "https://scale.com" + url
)

strategy = simple_scrape
