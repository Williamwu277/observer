from simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="OpenAI",
    base_url="https://openai.com/careers/search/",
    jobs_selector="#main a[href^='/careers']",
    url_selector=":scope",
    title_selector="h2",
    link_augmentation="https://openai.com",
)

strategy = simple_scrape
