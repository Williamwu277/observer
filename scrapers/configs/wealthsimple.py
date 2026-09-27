from strategies.ashby import AshbyScrapeConfig
from strategies.simple_scrape import simple_scrape


config = AshbyScrapeConfig(
    company_name="wealthsimple",
    base_url="https://jobs.ashbyhq.com/wealthsimple?employmentType=Intern",
)

strategy = simple_scrape
