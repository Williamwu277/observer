from strategies.paginating_scrape import PaginatingScrapeConfig, paginating_scrape


config = PaginatingScrapeConfig(
    company_name="Amazon",
    base_url="https://www.amazon.jobs/content/en/career-programs/university/internships-for-students?country%5B%5D=US&country%5B%5D=CA&employment-type%5B%5D=Intern&category%5B%5D=Software+Development&category%5B%5D=Systems%2C+Quality%2C+%26+Security+Engineering",
    jobs_selector='ul[class*="jobs-module_root"] div[class*="header-module_root"]',
    url_selector="h3 a",
    title_selector="h3 a",
    next_page_selector="button[data-test-id='next-page']",
    link_augmentation="https://www.amazon.jobs/en"
)

strategy = paginating_scrape
