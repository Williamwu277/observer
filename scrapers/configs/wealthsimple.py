from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Wealthsimple",
    base_url="https://jobs.ashbyhq.com/wealthsimple?employmentType=Intern",
    jobs_selector="a[href^='/wealthsimple/']",
    url_selector=":scope",
    title_selector="h3",
    link_augmentation="https://jobs.ashbyhq.com",
)

strategy = simple_scrape
