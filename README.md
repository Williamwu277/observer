# Observer

Internship scraping rig

You can see the spreadsheet of internships [here](https://docs.google.com/spreadsheets/d/1uaIL-RzYQ-UVAvO1WBw-80VvS5ZJsFJDfAyMEDXLtJ4/edit?gid=0#gid=0&fvid=1229650299)

To view the table in sorted order, first make sure you are on a laptop. Then, click on the icon that looks like a calculator above the date scraped column. Finally, click on default order.

## Table of Contents
- [Setup](#setup)
- [Operation](#operation)
- [Contribution](#contribution)
- [Notes](#notes)
- [Todo](#todo)

## Setup

1. Grab a service account from GCP (with google sheets enabled) and edit the `SERVICE_ACCOUNT_FILE` variable in `const.py` to point to it
2. Create a spreadsheet, share it with your service account, and then create an `.env` file with `SPREADSHEET_ID`
3. Edit the spreadsheet with a table to look like the sample (or edit the constants)
4. Create a virtual python environment and pip install the `requirements.txt`
5. Run `playwright install` in the virtual environment

## Operation

1. You can start a run of every single company within `/configs` by calling `python scrape.py`
2. Otherwise, you can name the stem of each config file one by one after (e.g. `python scrape.py ramp`)

Details of each run will be stored within `/logs` in case you need to debug

## Outline

The idea behind the scraping framework is that each scrape has three states: Navigating to page, finding jobs, and filtering jobs. Navigating to the page and filtering jobs is the same for each integration. Thus, only finding the jobs ever needs to be changed for each portal. Additionally, we can further abstract away finding the jobs as portals usually follow a pattern. To accomplish this, each company has a config and a strategy. The strategy is the function which performs the find jobs scraping, while the config stores the unique selectors and variables for each site (so that strategies are reusable). In this case, the default strategy would be `simple_scrape.py`. For each company, the strategy is called with the `page` from Playwright and the config variable as the parameters

You can see the examples within `/config` to get an idea. To scrape a new company, you can create a new config that corresponds to an existing strategy (or create a new strategy)

## Notes

Currently, there are a number of techniques employed to avoid the automated bot detection

1. The scraper is run in _headless but also not headless_ mode ... don't ask ... Roblox needs it
2. The user agent is randomly chosen
3. There is a slight delay between each action and each run
4. Playwright stealth mode is used

The reason this is a locally run script is because bot detection is less strict on local ip addresses. Hosting on the cloud results in data center ip addresses and much more scrutiny. You'd probably have to get a proxy in order to get that to work ...

Additionally, ip addresses have reputations. You should only scrape so many sites within a short time period

Finally, there are some portals that are noticeably absent from the list of configs. For example, Google. The problem is that Google has extremely sophisticated anti-bot detection systems (they have the money to do so) and they make it really obvious they don't want scraping (css selectors are obfuscated).

## Todo

1. Randomize the viewport
2. Port onto the cloud (makes it infinitely harder)
3. Add more companies
4. Make the code more resilient 
5. Add ghost cursor (manually move the mouse like a human) and human type (randomized delays between each key press)