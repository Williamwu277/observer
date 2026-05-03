import os
import requests
import logging
from dotenv import load_dotenv
from typing import Dict


logger = logging.getLogger(__name__)


load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')


def send_discord_message(message: Dict[str, str]) -> bool:
    """
    Send a message to the Discord webhook
    """
    if DISCORD_WEBHOOK_URL:
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json={
                "content": "@everyone",
                "embeds": [message],
                "allowed_mentions": {
                    "parse": ["everyone"]
                }
            })
            if response.status_code != 204:
                logger.error(f"Failed to send Discord message: {response}")
            else:
                return True
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
    else:
        logger.warning("No Discord webhook URL found")

    return False