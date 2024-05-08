from fastapi import status
from fastapi.testclient import TestClient


def test_get_all_when_ok(client: TestClient, user_header_token, event_service_mock):
    response = client.get("/api/v1/events", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert event_service_mock.all.call_count == 1


def test_get_when_ok(client: TestClient, event_service_mock, user_header_token):
    response = client.get("/api/v1/events/import_id", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "import_id"
    assert event_service_mock.get.call_count == 1


def test_get_when_not_found(client: TestClient, event_service_mock, user_header_token):
    event_service_mock.missing = True
    response = client.get("/api/v1/events/event1", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Event not found: event1"
    assert event_service_mock.get.call_count == 1
