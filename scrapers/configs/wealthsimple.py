from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="wealthsimple",
    base_url="https://jobs.ashbyhq.com/wealthsimple?employmentType=Intern",
    jobs_selector="a[href^='/wealthsimple/']",
    url_selector=":scope",
    title_selector="h3",
    link_augmentation=lambda url: "https://jobs.ashbyhq.com" + url,
    empty_portal_selector="span.ashby-job-board-heading-count:has-text('(0)')"
)

strategy = simple_scrape
