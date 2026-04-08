# --------------------------------------- Job Search Filters -----------------------------------------

LOCATION_WHITELIST = [
    "toronto", "vancouver", "san francisco", "new york", "california", "san matteo", 
    "british columbia", "seattle", "atlanta", "chicago", "los angeles", "washington",
    "united states", "canada", "sunnyvale", "mountain view"
]

LOCATION_BLACKLIST = ["london", "united kingdom"]

TITLE_WHITELIST = [
    "software", "engineer", "developer", "machine learning", "ai", "artificial intelligence"
]

TITLE_BLACKLIST = [
    "phd"
]


# --------------------------------------- Scraping Constants -----------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# -------------------------------------------- Sheet Constants --------------------------------------------

SERVICE_ACCOUNT_FILE = "../credentials.json"

RANGE_NAME = "2026!A2:E"

SPREADSHEET_COLUMN_MAP = {
    "Date Scraped": 0,
    "Company": 1,
    "Title": 2,
    "Url": 3,
    "Status": 4
}
