import os
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv
from typing import Dict, List


logger = logging.getLogger(__name__)


load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DISCORD_ROLE_ID = "1519577748077678642"
RETRY_CONFIG = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=frozenset(["POST"]),
    respect_retry_after_header=True,
    raise_on_status=False,
)

_adapter = HTTPAdapter(max_retries=RETRY_CONFIG)
session = requests.Session()
session.mount("https://", _adapter)
session.mount("http://", _adapter)


def send_discord_update(messages: List[Dict[str, str]]) -> bool:
    """
    Send a message to the Discord webhook

    Args: 
        messages: List of Discord embed dicts with title, url and description fields. 
            Up to 10 can be sent at a time maximum.

    Returns:
        True or false depending on whether the message was sent successfully
    """
    if not DISCORD_WEBHOOK_URL:
        logger.warning("No Discord webhook URL found")
        return False

    try:
        response = session.post(
            DISCORD_WEBHOOK_URL, 
            json={
                "content": f"<@&{DISCORD_ROLE_ID}>",
                "embeds": messages,
                "allowed_mentions": {
                    "roles": [DISCORD_ROLE_ID]
                }
            },
            timeout=(5, 10),
        )

        if response.status_code != 204:
            logger.error(f"Failed to send Discord message: {response.status_code} {response.text}")
            return False

    except Exception:
        logger.error("Failed to send Discord message", exc_info=True)
        return False

    return True
