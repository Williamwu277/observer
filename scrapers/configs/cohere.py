from strategies.ashby import AshbyScrapeConfig
from strategies.simple_scrape import simple_scrape


config = AshbyScrapeConfig(
    company_name="cohere",
    base_url="https://jobs.ashbyhq.com/cohere?employmentType=Intern",
)

strategy = simple_scrape
