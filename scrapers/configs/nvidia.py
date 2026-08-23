from strategies.paginating_scrape import PaginatingScrapeConfig, paginating_scrape


config = PaginatingScrapeConfig(
    company_name="nvidia",
    base_url="https://jobs.nvidia.com/careers?start=0&sort_by=timestamp&filter_job_type=intern+%28fixed+term%29",
    jobs_selector='div[data-test-id="job-listing"]',
    url_selector="a",
    title_selector="a",
    location_selector="a",
    next_page_selector="button[aria-label='Next jobs']",
    link_augmentation=lambda url: "https://jobs.nvidia.com" + url,
)

strategy = paginating_scrape
