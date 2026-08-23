# --------------------------------------- Job Search Filters -----------------------------------------

LOCATION_WHITELIST = [
    "toronto",
    "vancouver",
    "san francisco",
    "new york",
    "california",
    "san matteo",
    "british columbia",
    "seattle",
    "atlanta",
    "chicago",
    "los angeles",
    "washington",
    "united states",
    "canada",
    "sunnyvale",
    "mountain view",
    "santa clara"
]

LOCATION_BLACKLIST = ["london", "united kingdom"]

TITLE_WHITELIST = [
    "software",
    "engineer",
    "developer",
    "machine learning",
    "ai",
    "artificial intelligence",
]

TITLE_BLACKLIST = ["phd"]


# --------------------------------------- Scraping Constants -----------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# Fixed viewport so full-page screenshots stay comparable between runs
VIEWPORT = {"width": 1920, "height": 1080}

# -------------------------------------------- Sheet Constants --------------------------------------------

SERVICE_ACCOUNT_FILE = "../credentials.json"

INTERNSHIP_RANGE = "2026!A2:E"
STATUS_RANGE = "Status!A3:G"

DATA_MAP = {"Date Scraped": 0, "Company": 1, "Title": 2, "Url": 3, "Status": 4}
STATUS_DATA_MAP = {
    "Name": 0,
    "Portal": 1,
    "Status": 2,
    "Last Updated": 3,
    "Scrape Time": 4,
    "Request Size": 5,
    "pHash": 6,
}


# ------------------------------------------- Experimental Constants -------------------------------------------

P_HASH_THRESHOLD = 4
