from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="datadog",
    base_url="https://careers.datadoghq.com/all-jobs/?time_type%5B0%5D=Early%20Career&parent_department_Engineering%5B0%5D=Engineering",
    jobs_selector="li.ais-Hits-item",
    url_selector="a",
    title_selector="h3",
    link_augmentation=lambda url: "https://careers.datadoghq.com" + url
)

strategy = simple_scrape
