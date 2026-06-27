from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape


config = SimpleScrapeConfig(
    company_name="Vercel",
    base_url="https://vercel.com/careers?location=United+States&function=Engineering",
    jobs_selector='a[href^="/careers/"]',
    url_selector=":scope",
    title_selector="div p:nth-child(1)",
    link_augmentation=lambda url: "https://vercel.com" + url,
)

strategy = simple_scrape
