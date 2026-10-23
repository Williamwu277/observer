# Observer

<p align="center">
  <img src="assets/ObserverLogo.png" alt="Observer logo" width="600">
</p>

Observer is a reliability-focused internship discovery service. It checks public careers pages once per day, filters for relevant software engineering internships in the U.S. and Canada, and publishes new opportunities to Google Sheets and Discord. A reusable scraping framework, integration health tracking, and automated page-change detection keep the directory useful as careers sites evolve.

You can see the spreadsheet of internships as well as the entire directory [here](https://docs.google.com/spreadsheets/d/1uaIL-RzYQ-UVAvO1WBw-80VvS5ZJsFJDfAyMEDXLtJ4/edit?gid=0#gid=0&fvid=1229650299). 

## Table of Contents
- [Setup](#setup)
- [Operation](#operation)
- [Documentation](#documentation)
- [Todo](#todo)

## Setup

1. Grab a service account from GCP (with google sheets enabled) and edit the `SERVICE_ACCOUNT_FILE` variable in `const.py` to point to the credentials file
2. Create a spreadsheet, share it with your service account, and then create an `.env` file with `SPREADSHEET_ID`
3. Edit the spreadsheet with a jobs table using these columns: `Date Scraped | Company | Title | Url | Location | Status`.
4. Add the Discord webhooks `ANNOUNCEMENTS_WEBHOOK_URL` and `ERRORS_WEBHOOK_URL` to your `.env` file for notifications. You can also add `SUMMARY_WEBHOOK_URL` to post the end-of-run summary to a separate channel.
5. To use an external Playwright Server, set `PLAYWRIGHT_SERVER_URL` in `.env`. Leave it unset to run Chromium locally.
6. Create a virtual python environment and pip install the `requirements.txt`
7. Run `playwright install` in the virtual environment

## Operation

1. You can start a run of every single company within `/configs` by calling `python scrape.py`
2. Otherwise, you can name the stem of each config file one by one (e.g. `python scrape.py ramp rippling`)
3. If you do not want discord notifications to run, you can add a `-T` argument for debug mode (e.g. `python scrape.py -T ramp`)

Details of each run will be stored within `/logs` in case you need to debug

### Docker

Published images use the same repository, `ghcr.io/williamwu277/observer`:

| Browser mode | Moving tag | Commit tag | Docker build target |
| --- | --- | --- | --- |
| Bundled Chromium | `latest` | `<commit-sha>` | `local` |
| External Playwright Server | `remote` | `<commit-sha>-remote` | `remote` |

The publish workflow builds both variants. Its `tag_latest` option controls whether both moving tags are updated; commit tags are always published. Existing `latest` and commit tags continue to include Chromium.

For the bundled browser, use the credentials and `.env` file from Setup:

```bash
docker run --rm --init --ipc=host \
  --env-file .env \
  -v "$(pwd)/credentials.json:/app/credentials.json:ro" \
  ghcr.io/williamwu277/observer:latest
```

To run Chromium separately, start a matching Playwright Server on a private network:

```bash
docker network create observer
docker run -d --name observer-browser --network observer --init --ipc=host \
  --workdir /home/pwuser --user pwuser \
  mcr.microsoft.com/playwright:v1.61.0-noble \
  /bin/sh -c "npx -y playwright@1.61.0 run-server --port 3000 --host 0.0.0.0"

docker run --rm --init --network observer \
  --env-file .env \
  -v "$(pwd)/credentials.json:/app/credentials.json:ro" \
  -e PLAYWRIGHT_SERVER_URL=ws://observer-browser:3000/ \
  ghcr.io/williamwu277/observer:remote
```

The remote image requires `PLAYWRIGHT_SERVER_URL`; it contains no browser binaries. The remote server must stay on a private network and must use the same Playwright major and minor version as the client. The client is pinned to `1.61.0` in `requirements.txt`; update that pin and the server image/package together.

For local builds:

```bash
docker build --target local -t observer:local .
docker build --target remote -t observer:remote .
```

An untargeted `docker build` also builds `local`, the final stage. To select scrapers, override the container command with `python scrape.py roblox` after the image name. Add a volume at `/app/scrapers/logs` to retain logs after the container exits.

## Documentation

- [The Scraping Framework](#1-the-scraping-framework)
- [Scraping Careers Sites](#2-scraping-careers-sites)
- [Scraper Statuses](#3-scraper-statuses)
- [Automated Change Detection](#4-automated-change-detection)
- [Responsible Scraping](#5-responsible-scraping)

#### 1. The Scraping Framework

Each module in `configs` exports a `config` and `strategy`. `scrape_integration`
selects a pipeline from the config type. Browser integrations use:

- `NAVIGATING_TO_PORTAL` opens the careers page and optionally accepts its cookie prompt.
- `FINDING_JOBS` runs the integration's browser strategy.
- `POST_SCRAPE_ACTION` handles empty portals and optional screenshot evidence.
- `FILTERING_JOBS` applies the shared title and location filters.

The only API integration currently supported is Greenhouse. It requests the
configured endpoint and parses its JSON response:

- `REQUESTING_API` makes the request and decodes the response.
- `FINDING_JOBS` and `FILTERING_JOBS` convert and filter jobs as described above.

#### 2. Scraping Careers Sites

##### Browser integrations

Use `simple_scrape` for a single job list, including lists revealed by a section
or load-more button. Use `paginating_scrape` for portals with multiple pages.
For example:

```python
# ramp.py
from strategies.simple_scrape import SimpleScrapeConfig, simple_scrape

config = SimpleScrapeConfig(
    company_name="ramp",
    base_url="https://ramp.com/careers",
    jobs_selector="section#jobs div[data-state] a",
    url_selector=":scope",
    title_selector=":scope",
    section_click_name="Emerging Talent",
)

strategy = simple_scrape
```

A custom browser strategy receives its config and Playwright page and returns
the collected jobs:

```python
def custom_scrape(
    config: BrowserScrapeConfig,
    page: Page,
) -> dict[str, list[ScrapeResult]]:
    return {"jobs": jobs}
```

##### Ashby

For `jobs.ashbyhq.com`, use `AshbyScrapeConfig` with `simple_scrape` to reuse
the shared selectors.

##### Greenhouse API scraping

Greenhouse integrations provide the public careers URL and API endpoint, then
use the shared strategy:

```python
from models import GreenhouseScrapeConfig
from strategies.greenhouse import greenhouse_scrape

config = GreenhouseScrapeConfig(
    company_name="discord",
    base_url="https://discord.com/careers",
    api_url="https://api.greenhouse.io/v1/boards/discord/jobs",
)

strategy = greenhouse_scrape
```

`base_url` is the public careers page used for status reporting. `api_url` is
the Greenhouse endpoint. The optional `link_augmentation` field on
`BaseScrapeConfig` converts source URLs into the canonical URLs stored by
Observer.

#### 3. Scraper Statuses

After a scraping run, you may see the status page on the spreadsheet. A scraping integration can have statuses of:

- `Operational` means that the scraper completed successfully, including when its jobs are filtered out or a validated feed confirms that no jobs are available
- `Confident` means that though the scraper may not be finding any job listings, the automated portal change detection system has determined that there has probably been no changes
- `Questionable` means that the scraper is not finding any job listings on the portal. Someone should take a look to make sure that is the correct behaviour
- `Down` means that something has changed or the scraper is erroring out

`IncompleteScrapeError` means a scraper could not confirm that it collected the
complete job list.

Only `Operational` or `Confident` runs update jobs and announce new listings on
Discord. Missing listings expire; `Questionable` and `Down` runs leave jobs unchanged.

Usually, integrations should be `Operational` or `Confident`. A browser scraper
that finds no source jobs becomes `Questionable`; a validated empty API feed or
a successful scrape whose jobs are all filtered out remains `Operational`.

#### 4. Automated Change Detection

This is an experimental feature for browser integrations with `empty_portal_selector` enabled. When no source jobs are found, it scrolls to that element and takes a screenshot of the page. If the screenshots from run to run are similar (using pHashing to determine similarity), there is a pretty high chance that the portal is still the same.

When an eligible browser integration finds no source jobs, it is set to `Questionable`. You can inspect the portal and mark the scraper `Confident` if it is still correct. This starts the automated pHash tracking process. If a later screenshot differs beyond the threshold, the scraper is set to `Down` for another review.

Why this strategy in particular? The main idea is that we want to be as sure as possible that we aren't missing anything without having to check daily. We've accepted the odds for false positive notifications of the portal breaking; however, the worst case scenario that we prevent (as much as we can) is when it says a scraper is operational but in reality isn't. Additionally, consider this scenario (which happened). The Uber careers page changed formats. However, the link in the config still yields a valid page. The page displays no jobs since the queries in the link point to invalid sources. I believe this screenshot strategy will notice the portal change, while other strategies are less likely to.

#### 5. Responsible Scraping

Observer is designed as a low-frequency discovery service, not a general-purpose crawler. Each configured careers page is checked once per day, and scraping integrations are not automatically retried when they fail. Failed or changed integrations are surfaced for human review instead of being repeatedly requested.

Integrations read publicly available job listings and minimize their interaction with each page. A typical integration navigates to a careers page and extracts the visible listing data, using only the clicks, scrolling, or pagination needed to reveal those listings or confirm that a result set is empty. Observer does not submit applications, authenticate as candidates, collect candidate information, or continuously poll careers sites.

The project favors public APIs and structured job-board endpoints when they are available. New integrations are intended to remain limited to public careers information.

## Todo

- [ ] Extend company directory 
- [ ] Concurrently scrape
- [ ] Refactor code to be cleaner
