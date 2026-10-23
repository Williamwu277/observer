import json
import logging
import os
from collections.abc import Callable, Generator
from contextlib import contextmanager
from random import choice

import requests
from const import USER_AGENTS, VIEWPORT
from playwright.sync_api import Browser, Page, Playwright
from playwright_stealth import Stealth
from utils import attach_network_monitor

logger = logging.getLogger(__name__)


def start_browser(playwright: Playwright) -> Browser:
    """
    Launch full Chromium locally or through a compatible Playwright Server.
    """
    server_url = os.getenv("PLAYWRIGHT_SERVER_URL")
    if server_url:
        logger.info("Connecting to remote Playwright Server")
        return playwright.chromium.connect(
            server_url,
            timeout=30_000,
            headers={
                "x-playwright-launch-options": json.dumps(
                    {"channel": "chromium", "headless": True}
                )
            },
        )

    logger.info("Launching local Chromium")
    # headless=False and args=["--headless=new"] avoid roblox not loading for some reason
    return playwright.chromium.launch(headless=False, args=["--headless=new"])


class ResourceManager:
    """
    Lazily create and close resources shared across scraper integrations.
    """

    def __init__(self, playwright: Playwright):
        self._playwright = playwright
        self._browser: Browser | None = None
        self._http_client: requests.Session | None = None
        self._get_browser_bytes: Callable[[], int] = lambda: 0
        self._api_bytes = 0

    def get_browser(self) -> Browser:
        if self._browser is None:
            self._browser = start_browser(self._playwright)
        return self._browser

    def get_http_client(self) -> requests.Session:
        if self._http_client is None:
            self._http_client = requests.Session()
        return self._http_client

    @contextmanager
    def browser_page(self) -> Generator[Page, None, None]:
        context = self.get_browser().new_context(
            user_agent=choice(USER_AGENTS),
            viewport=VIEWPORT,
        )
        try:
            page = context.new_page()
            Stealth().apply_stealth_sync(page)
            self._get_browser_bytes = attach_network_monitor(
                context.new_cdp_session(page)
            )
            yield page
        finally:
            context.close()

    def reset_transferred_bytes(self) -> None:
        self._get_browser_bytes = lambda: 0
        self._api_bytes = 0

    def record_api_response(self, response: requests.Response) -> None:
        self._api_bytes += len(response.content)

    def get_transferred_bytes(self) -> int:
        return self._get_browser_bytes() + self._api_bytes

    def close(self) -> None:
        if self._http_client is not None:
            self._http_client.close()
        if self._browser is not None:
            self._browser.close()
