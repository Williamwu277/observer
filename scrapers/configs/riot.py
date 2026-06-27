from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Riot",
    base_url="https://www.riotgames.com/en/student-internships#",
    jobs_selector="div.job-list li.job-row a",
    url_selector=":scope",
    title_selector="div:nth-child(1)",
    location_selector="div:nth-child(4)",
    link_augmentation=lambda id: f"https://www.riotgames.com/en/work-with-us/job/{id.split('/')[-1]}"
)

strategy = simple_scrape
