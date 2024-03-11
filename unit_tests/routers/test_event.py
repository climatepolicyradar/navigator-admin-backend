import logging

import pytest
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

import app.service.event as event_service
from unit_tests.helpers.event import create_event_create_dto, create_event_write_dto


def test_get_all_when_ok(client: TestClient, user_header_token, event_service_mock):
    response = client.get("/api/v1/events", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
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
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert event_service_mock.search.call_count == 1


def test_search_when_invalid_params(
    client: TestClient, event_service_mock, user_header_token
):
    response = client.get("/api/v1/events/?wrong=yes", headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"
    assert event_service_mock.search.call_count == 0


def test_search_when_db_error(
    client: TestClient, event_service_mock, user_header_token
):
    event_service_mock.throw_repository_error = True
    response = client.get("/api/v1/events/?q=error", headers=user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "bad repo"
    assert event_service_mock.search.call_count == 1


def test_search_when_request_timeout(
    client: TestClient,
    event_service_mock,
    user_header_token,
    caplog,
):
    event_service_mock.throw_timeout_error = True
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/events/?q=timeout", headers=user_header_token)
    assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
    assert event_service_mock.search.call_count == 1
    assert (
        "Request timed out fetching matching events. Try adjusting your query."
        in caplog.text
    )


def test_search_when_not_found(
    client: TestClient, event_service_mock, user_header_token, caplog
):
    event_service_mock.missing = True
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/events/?q=stuff", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    response.json()
    assert event_service_mock.search.call_count == 1
    assert (
        "Events not found for terms: {'q': 'stuff', 'max_results': 500}" in caplog.text
    )


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


def test_update_when_ok(client: TestClient, event_service_mock, user_header_token):
    new_data = create_event_write_dto("event1")
    response = client.put(
        "/api/v1/events/E.0.0.1",
        json=jsonable_encoder(new_data),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "E.0.0.1"
    assert event_service_mock.update.call_count == 1


def test_update_when_not_found(
    client: TestClient, event_service_mock, user_header_token
):
    event_service_mock.missing = True
    new_data = create_event_write_dto("event1")
    response = client.put(
        "/api/v1/events/a.b.c.d",
        json=jsonable_encoder(new_data),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Event not updated: a.b.c.d"
    assert event_service_mock.update.call_count == 1


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
