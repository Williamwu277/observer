from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="atlassian",
    base_url="https://www.atlassian.com/company/careers/all-jobs?team=Interns&location=&search=",
    jobs_selector="a[href*='/company/careers/details/']",
    url_selector=":scope",
    title_selector=":scope",
    link_augmentation=lambda url: "https://www.atlassian.com" + url
)

strategy = simple_scrape
