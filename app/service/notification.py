import logging
import os

from notify.slack import slack_message

_LOGGER = logging.getLogger(__name__)


def send_notification(notification: str):
    try:
        if os.environ["SLACK_WEBHOOK_URL"] != "skip":
            slack_message(notification)
        _LOGGER.info(notification)
    except Exception as e:
        _LOGGER.error(f"Error sending notification caused by: {e}")
