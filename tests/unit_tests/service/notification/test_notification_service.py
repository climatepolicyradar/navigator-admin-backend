import logging
from unittest.mock import patch

from app.service.notification import send_notification


def test_send_notification_success(caplog, monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "test")

    notification = "Hello World!"

    with (
        caplog.at_level(logging.INFO),
        patch("app.service.notification.slack_message") as slack_mock,
    ):
        send_notification(notification)

    slack_mock.assert_called_once_with(notification)
    assert notification in caplog.text


def test_send_notification_error(caplog, monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "test")

    exception_message = "Test error"

    with (
        caplog.at_level(logging.ERROR),
        patch(
            "app.service.notification.slack_message",
            side_effect=Exception(exception_message),
        ),
    ):
        send_notification("Hello World!")

    assert f"Error sending notification caused by: {exception_message}" in caplog.text


def test_do_not_send_notification_when_in_local_development(caplog):
    notification = "Hello World!"

    with (
        caplog.at_level(logging.INFO),
        patch("app.service.notification.slack_message") as slack_mock,
    ):
        send_notification(notification)

    slack_mock.assert_not_called()
    assert notification in caplog.text
