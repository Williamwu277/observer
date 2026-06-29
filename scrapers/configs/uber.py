from strategies.paginating_scrape import PaginatingScrapeConfig, paginating_scrape


config = PaginatingScrapeConfig(
    company_name="Uber",
    base_url="https://jobs.uber.com/en/jobs/?location=San+Francisco&radius=60&lat=37.7749295&lng=-122.41941550000001&team=University&subTeam=Engineering",
    jobs_selector="div#js-job-search-results > div",
    url_selector="a",
    title_selector="a",
    next_page_selector="a[aria-label='Go to next page']",
    link_augmentation=lambda url: "https://jobs.uber.com" + url,
    cookies_accept_text="Accept All",
)

strategy = paginating_scrape
