import logging
import os
from typing import Optional

from slack_sdk.web.client import WebClient

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


def send_notification(
    notification: str, thread_ts: Optional[str] = None
) -> Optional[str]:
    """
    Sends Slack notification to a channel specified in the environment variables.
    Does not send a notification if the value of the SLACK_OAUTH_TOKEN env variable is set to "skip".
    If a thread_ts is passed in, it can be used to post messages to the same thread.

    :param str notification: The notification to be sent to Slack.
    :param Optional[str] thread_ts: The thread identifier.
    :return Optional[str]: The timestamp of the posted message.
    """
    try:
        _LOGGER.info(notification)
        if os.environ["SLACK_OAUTH_TOKEN"] != "skip":
            client = WebClient(token=os.environ["SLACK_OAUTH_TOKEN"])

            response = client.chat_postMessage(
                channel=os.environ["SLACK_CHANNEL"],
                text=notification,
                thread_ts=thread_ts,
            )

            return response["ts"]

    except Exception as e:
        _LOGGER.error(f"Error sending notification caused by: {e}")
