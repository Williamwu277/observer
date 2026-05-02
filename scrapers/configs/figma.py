from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Figma",
    base_url="https://www.figma.com/careers/#job-openings",
    jobs_selector="div:has(> h2#early-career) a",
    url_selector=":scope",
    title_selector="span",
    #location_selector="span",
)

strategy = simple_scrape
