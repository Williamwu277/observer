from strategies.paginating_scrape import PaginatingScrapeConfig, paginating_scrape


config = PaginatingScrapeConfig(
    company_name="Pinterest",
    base_url="https://www.pinterestcareers.com/jobs/?search=&team=University&pagesize=20#results",
    jobs_selector='div.job-listing div.card-job',
    url_selector="a",
    title_selector="a",
    location_selector="li:nth-child(1)",
    next_page_selector="a[aria-label='Next page']",
    link_augmentation="https://www.pinterestcareers.com"
)

strategy = paginating_scrape
