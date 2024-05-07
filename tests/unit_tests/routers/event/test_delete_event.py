import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_delete_when_ok(
    client: TestClient, event_service_mock, admin_user_header_token
):
    response = client.delete("/api/v1/events/event1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert event_service_mock.delete.call_count == 1


@pytest.mark.skip(reason="No admin user for MVP")
def test_delete_event_fails_if_not_admin(
    client: TestClient, event_service_mock, user_header_token
):
    response = client.delete("/api/v1/events/event1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert event_service_mock.delete.call_count == 0


def test_delete_when_not_found(
    client: TestClient, event_service_mock, admin_user_header_token
):
    event_service_mock.missing = True
    response = client.delete("/api/v1/events/event1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Event not deleted: event1"
    assert event_service_mock.delete.call_count == 1
