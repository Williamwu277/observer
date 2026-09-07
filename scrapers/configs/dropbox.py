from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="dropbox",
    base_url="https://www.dropbox.jobs/en/jobs/?search=intern&pagesize=20#results",
    jobs_selector='div.job-listing',
    url_selector="a",
    title_selector="a",
    link_augmentation=lambda url: "https://www.dropbox.jobs" + url
)

strategy = simple_scrape
