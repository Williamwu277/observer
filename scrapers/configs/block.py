from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="block",
    base_url="https://block.xyz/careers/jobs?employeeTypes[]=Intern",
    jobs_selector="div.jobs-stack a",
    url_selector=":scope",
    title_selector="> div:nth-child(2)",
    link_augmentation=lambda url: "https://block.xyz" + url
)

strategy = simple_scrape
