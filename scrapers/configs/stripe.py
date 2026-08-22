from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="stripe",
    base_url="https://stripe.com/careers/search?employment_types=Intern",
    jobs_selector="div.careers-role-result__container",
    url_selector="a.careers-role-result__title",
    title_selector="a.careers-role-result__title",
    location_selector="span.careers-role-result__metadata-location",
    link_augmentation=lambda url: "https://stripe.com" + url
)

strategy = simple_scrape
