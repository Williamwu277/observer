import os
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv
from typing import Dict, List
from enum import Enum, auto


logger = logging.getLogger(__name__)


load_dotenv()


class WebhookType(Enum):
    ANNOUNCEMENTS = auto()
    ERRORS = auto()


webhook_urls = {
    WebhookType.ANNOUNCEMENTS: os.getenv("ANNOUNCEMENTS_WEBHOOK_URL"),
    WebhookType.ERRORS: os.getenv("ERRORS_WEBHOOK_URL"),
}

role_ids = {
    WebhookType.ANNOUNCEMENTS: "1519577748077678642",
    WebhookType.ERRORS: "1521030700780753037",
}

MAX_EMBEDS_PER_MESSAGE = 10
MAX_EMBED_DESCRIPTION_LENGTH = 4000
MAX_TIMEOUT = 10
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


def send_discord_update(
    webhook_type: WebhookType, messages: List[Dict[str, str]]
) -> bool:
    f"""
    Send a message to the Discord webhook

    Args: 
        messages: List of Discord embed dicts with title, url and description fields. 
            Up to {MAX_EMBEDS_PER_MESSAGE} can be sent at a time maximum.

    Returns:
        True or false depending on whether the message was sent successfully
    """
    if not webhook_urls[webhook_type]:
        logger.warning("No Discord webhook URL found")
        return False

    try:
        response = session.post(
            webhook_urls[webhook_type],
            json={
                "content": f"<@&{role_ids[webhook_type]}>",
                "embeds": messages,
                "allowed_mentions": {"roles": [role_ids[webhook_type]]},
            },
            timeout=MAX_TIMEOUT,
        )

        if response.status_code != 204:
            logger.error(
                "Failed to send Discord message: %s %s",
                response.status_code,
                response.text,
            )
            return False

    except Exception:
        logger.error("Failed to send Discord message", exc_info=True)
        return False

    return True


def send_discord_batch_update(
    webhook_type: WebhookType, internship_list: List[Dict[str, str]]
) -> bool:
    """
    Send all the internship updates to the Discord webhook

    Args:
        messages: List of Discord embed dicts with title, url and description fields.

    Returns:
        True or false depending on whether the messages were sent successfully
    """
    send_queue = []
    for i, message in enumerate(internship_list):
        send_queue.append(message)
        if len(send_queue) == MAX_EMBEDS_PER_MESSAGE or i == len(internship_list) - 1:
            status = send_discord_update(webhook_type, send_queue)
            send_queue = []
            # If the message fails the exponential retries, accept the loss and back off
            if not status:
                return False

    return True
