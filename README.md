# Observer

Internship scraper.

You can see the spreadsheet of internships as well as the entire directory [here](https://docs.google.com/spreadsheets/d/1uaIL-RzYQ-UVAvO1WBw-80VvS5ZJsFJDfAyMEDXLtJ4/edit?gid=0#gid=0&fvid=1229650299). 

## Table of Contents
- [Setup](#setup)
- [Operation](#operation)
- [Documentation](#documentation)
- [Todo](#todo)

## Setup

1. Grab a service account from GCP (with google sheets enabled) and edit the `SERVICE_ACCOUNT_FILE` variable in `const.py` to point to the credentials file
2. Create a spreadsheet, share it with your service account, and then create an `.env` file with `SPREADSHEET_ID`
3. Edit the spreadsheet with a table to look like the sample (or edit the constants)'
4. Add the Discord webhooks `ANNOUNCEMENTS_WEBHOOK_URL` and `ERRORS_WEBHOOK_URL` to your `.env` file for notifications. You can also add `SUMMARY_WEBHOOK_URL` to post the end-of-run summary to a separate channel.
5. Create a virtual python environment and pip install the `requirements.txt`
6. Run `playwright install` in the virtual environment

## Operation

1. You can start a run of every single company within `/configs` by calling `python scrape.py`
2. Otherwise, you can name the stem of each config file one by one (e.g. `python scrape.py ramp rippling`)
3. If you do not want discord notifications to run, you can add a `-T` argument for debug mode (e.g. `python scrape.py -T ramp`)

Details of each run will be stored within `/logs` in case you need to debug

## Documentation

- [The Scraping Framework](#1-the-scraping-framework)
- [Scraping Careers Sites](#2-scraping-careers-sites)
- [Scraper Statuses](#3-scraper-statuses)
- [Automated Change Detection](#4-automated-change-detection)
- [Bot Detection](#5-bot-detection)

#### 1. The Scraping Framework

The scraping framework is a state machine which cycles through the states:

- `NAVIGATING_TO_PORTAL` covers going to the URL of the company careers site and optionally accepting any cookie pop-ups
- `FINDING_JOBS` is the solely customizable state, where users can define a scraping strategy to find the jobs in that portal
- `POST_SCRAPE_ACTION` runs after all the jobs are found. Currently, it is used to optionally take a screenshot of the page for determining whether the portal has been updated in the case that no jobs were found
- `FILTERING_JOBS` takes the scraped jobs and ensures that the location and job title are correct (internships for software engineering roles at a U.S. or Canada location).

#### 2. Scraping Careers Sites

Continuing on the scraping strategies for the `FINDING_JOBS` state, currently there are two prewritten ones: `simple_scrape` and `paginating_scrape`. Simple scrape covers a wide variety of cases including optionally clicking something, optionally repeatedly clicking a button (e.g. more jobs), before extracting job data from a table. Paginating scrape is used in the case where there are multiple pages of jobs. For both of these strategies there is a `ScrapeConfig`, which stores the portal-specific data necessary for that portal (e.g. URL, selectors etc). The `FINDING_JOBS` state takes in both a strategy and a config, which you must provide as a file in the `configs` directory in order to successfully scrape a portal. For example:

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

This `Ramp` integration uses `simple_scrape` (as well as the corresponding `SimpleScrapeConfig`). It defines the URL to the portal as well as the selectors needed to find the job posting information. As well, it makes use of the optional click at the beginning of a simple scrape (`section_click_name`).

In the event that neither simple scrape nor paginating scrape can fulfill your use-case, you can define your own scraping strategy (and config) and set the `strategy` and `config` variables to it in your file. You must adhere to the following function signature below:

```python
def <insert_function_name>(config: <insert_config_type>, page: Page) -> dict[str, List[ScrapeResult]]:

# Returns {"jobs": List[ScrapeResult]}
```

#### 3. Scraper Statuses

After a scraping run, you may see the status page on the spreadsheet. A scraping integration can have statuses of:

- `Operational` means that the scraper is finding job listings on the career site (even if it gets filtered out later by title). This gives us a very high confidence level of the operation of the scraper
- `Confident` means that though the scraper may not be finding any job listings, the automated portal change detection system has determined that there has probably been no changes
- `Questionable` means that the scraper is not finding any job listings on the portal. Someone should take a look to make sure that is the correct behaviour
- `Down` means that something has changed or the scraper is erroring out

Usually, it is optimal for all the integrations to be `Operational` or `Confident`. When a scraper run yields no results, the status will be set to `Questionable`.

#### 4. Automated Change Detection

This is a new experimental feature for integrations with `empty_portal_selector` enabled. When no job listings are found, it scrolls to that element and takes a screenshot of the page. If the screenshots from run to run are similar (using pHashing to determine similarity), there is a pretty high chance that the portal is still the same. 

On a day-to-day basis, when a run yields no results, the integration is set to `Questionable`. Then, you can look at the portal to determine whether or not anything is amiss. If everything is fine, you should set the status of the scraper to `Confident`. This starts the automated pHash tracking process. If at any time the pHash comparisons yield large differences, the scraper status will be set to `Down` for another human look.

Why this strategy in particular? The main idea is that we want to be as sure as possible that we aren't missing anything without having to check daily. We've accepted the odds for false positive notifications of the portal breaking; however, the worst case scenario that we prevent (as much as we can) is when it says a scraper is operational but in reality isn't. Additionally, consider this scenario (which happened). The Uber careers page changed formats. However, the link in the config still yields a valid page. The page displays no jobs since the queries in the link point to invalid sources. I believe this screenshot strategy will notice the portal change, while other strategies are less likely to.

#### 5. Bot Detection

Web scraping is a cat and mouse game between anti-bot detection and also the stealth functionalities of a scraper. In this project, there are a few preventative measures:

- Playwright stealth
- Variable delays
- Few to no interactions with the page

We also run it on a residential IP just once a day. However, this is nowhere near all the things that we could have done (I believe the residential IP is doing the hard-lifting here). We've also refrained from scraping sites that clearly do not wish to be scraped (Google source code is fully obfuscated).

## Todo

- [ ] Extend company directory 
- [ ] Add proxies to protect IP
- [ ] Concurrently scrape
- [ ] Enhance anti-bot detection measures
- [ ] Refactor code to be cleaner
