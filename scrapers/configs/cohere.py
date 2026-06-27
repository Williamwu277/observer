from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Cohere",
    base_url="https://jobs.ashbyhq.com/cohere?employmentType=Intern",
    jobs_selector="div[class='ashby-job-posting-brief-list'] a",
    url_selector=":scope",
    title_selector="h3",
    link_augmentation=lambda url: "https://jobs.ashbyhq.com" + url,
)

strategy = simple_scrape
