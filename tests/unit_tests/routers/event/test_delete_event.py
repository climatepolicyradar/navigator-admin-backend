from fastapi import status
from fastapi.testclient import TestClient


def test_delete_when_ok(client: TestClient, event_service_mock, user_header_token):
    response = client.delete("/api/v1/events/event1", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert event_service_mock.delete.call_count == 1


def test_delete_when_not_found(
    client: TestClient, event_service_mock, user_header_token
):
    event_service_mock.missing = True
    response = client.delete("/api/v1/events/event1", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Event not deleted: event1"
    assert event_service_mock.delete.call_count == 1


def test_delete_fails_when_invalid_org(
    client: TestClient, event_service_mock, user_header_token
):
    event_service_mock.throw_validation_error = True
    response = client.delete("/api/v1/events/event1", headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Validation error"


def test_delete_fails_when_org_mismatch(
    client: TestClient, event_service_mock, user_header_token
):
    event_service_mock.org_mismatch = True
    response = client.delete("/api/v1/events/event1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "Org mismatch"
    assert event_service_mock.delete.call_count == 1


def test_delete_success_when_org_mismatch_super(
    client: TestClient, event_service_mock, user_header_token
):
    event_service_mock.org_mismatch = True
    event_service_mock.superuser = True
    response = client.delete("/api/v1/events/event1", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert event_service_mock.delete.call_count == 1
