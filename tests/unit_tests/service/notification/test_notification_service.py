import logging
import os
from unittest.mock import patch

from app.service.notification import send_notification


@patch.dict(os.environ, {"SLACK_OAUTH_TOKEN": "test"})
def test_send_notification_success(caplog):
    notification = "Hello World!"

    with (
        caplog.at_level(logging.INFO),
        patch("app.service.notification.WebClient") as mock_client,
    ):

        mock_instance = mock_client.return_value
        mock_instance.chat_postMessage.return_value = {"ts": ""}

        send_notification(notification)

        mock_client.assert_called_once_with(token="test")
        mock_instance.chat_postMessage.assert_called_once_with(
            channel="updates-document-pipeline",
            text=notification,
            thread_ts=None,
        )

        assert notification in caplog.text


@patch.dict(os.environ, {"SLACK_OAUTH_TOKEN": "test"})
def test_send_notification_error(caplog):

    exception_message = "Test error"

    with (
        caplog.at_level(logging.ERROR),
        patch("app.service.notification.WebClient") as mock_client,
    ):

        mock_instance = mock_client.return_value
        mock_instance.chat_postMessage.side_effect = Exception(exception_message)

        send_notification("Hello World!")

        assert (
            f"Error sending notification caused by: {exception_message}" in caplog.text
        )


@patch.dict(os.environ, {"SLACK_OAUTH_TOKEN": "skip"})
def test_do_not_send_notification_when_in_local_development(caplog):
    notification = "Hello World!"

    with (
        caplog.at_level(logging.INFO),
        patch("app.service.notification.WebClient") as mock_client,
    ):

        mock_instance = mock_client.return_value
        mock_instance.chat_postMessage.return_value = {"ts": ""}

        send_notification("Hello World!")

        mock_client.assert_not_called()
        mock_instance.assert_not_called()
        assert notification in caplog.text
