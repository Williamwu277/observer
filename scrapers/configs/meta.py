from strategies.paginating_scrape import PaginatingScrapeConfig, paginating_scrape


config = PaginatingScrapeConfig(
    company_name="meta",
    base_url="https://www.metacareers.com/jobsearch/?roles[0]=Internship",
    jobs_selector="a[href^='/profile/job_details/']",
    url_selector=":scope",
    title_selector="h3",
    location_selector=":scope > div > div:first-child > div[aria-hidden='true'] + div",
    next_page_selector="[role='button'][aria-label='Button to select next week']",
    link_augmentation=lambda url: "https://www.metacareers.com" + url,
)

strategy = paginating_scrape
