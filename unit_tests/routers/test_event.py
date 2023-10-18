from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
import app.service.event as event_service

from unit_tests.helpers.event import (
    create_event_create_dto,
    # create_event_write_dto,
)


def test_get_all_when_ok(client: TestClient, user_header_token, event_service_mock):
    response = client.get("/api/v1/events", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert event_service.all.call_count == 1


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


def test_search_when_ok(client: TestClient, event_service_mock, user_header_token):
    response = client.get("/api/v1/events/?q=anything", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert event_service_mock.search.call_count == 1


def test_search_when_not_found(
    client: TestClient, event_service_mock, user_header_token
):
    event_service_mock.missing = True
    response = client.get("/api/v1/events/?q=stuff", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Events not found for term: stuff"
    assert event_service_mock.search.call_count == 1


def test_create_when_ok(client: TestClient, event_service_mock, user_header_token):
    new_data = create_event_create_dto("event1").model_dump()
    response = client.post(
        "/api/v1/events", json=jsonable_encoder(new_data), headers=user_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data == "new.event.id.0"
    assert event_service_mock.create.call_count == 1


def test_create_when_family_not_found(
    client: TestClient, event_service_mock, user_header_token
):
    event_service_mock.missing = True
    new_data = create_event_create_dto("this_family")
    response = client.post(
        "/api/v1/events", json=jsonable_encoder(new_data), headers=user_header_token
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Could not find family for this_family"
    assert event_service_mock.create.call_count == 1
