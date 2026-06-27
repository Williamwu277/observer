from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Roblox",
    base_url="https://careers.roblox.com/jobs?type=internship",
    jobs_selector="#jobs-filter a",
    url_selector=":scope",
    title_selector="p",
    link_augmentation=lambda url: "https://careers.roblox.com" + url
)

strategy = simple_scrape
