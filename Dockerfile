FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Connects to a separate Playwright Server through PLAYWRIGHT_SERVER_URL.
FROM base AS remote

COPY scrapers/ scrapers/

WORKDIR /app/scrapers

CMD ["python", "scrape.py"]


# Runs Chromium inside the container. This remains the default build target.
FROM base AS local

RUN playwright install --with-deps chromium

# Copy scraper source code
COPY scrapers/ scrapers/

WORKDIR /app/scrapers

# credentials.json is expected at /app/credentials.json (one level up from scrapers/)
# Mount it at runtime: -v /path/to/credentials.json:/app/credentials.json:ro
# Also mount .env: -v /path/to/.env:/app/scrapers/.env:ro

CMD ["python", "scrape.py"]
