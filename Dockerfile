FROM python:3.12-slim

# Install system dependencies required by Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    libxshmfence1 libx11-xcb1 fonts-liberation libdrm2 libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install chromium

# Copy scraper source code
COPY scrapers/ scrapers/

# Create logs directory
RUN mkdir -p scrapers/logs

WORKDIR /app/scrapers

# credentials.json is expected at /app/credentials.json (one level up from scrapers/)
# Mount it at runtime: -v /path/to/credentials.json:/app/credentials.json:ro
# Also mount .env: -v /path/to/.env:/app/scrapers/.env:ro

CMD ["python", "scrape.py"]
