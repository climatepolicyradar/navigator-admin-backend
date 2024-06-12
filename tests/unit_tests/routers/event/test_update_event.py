from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from tests.helpers.event import create_event_write_dto


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


def test_update_when_validation_error(
    client: TestClient, event_service_mock, user_header_token
):
    event_service_mock.throw_validation_error = True
    new_data = create_event_write_dto("event1")
    response = client.put(
        "/api/v1/events/E.0.0.1",
        json=jsonable_encoder(new_data),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Validation error"
    assert event_service_mock.update.call_count == 1


def test_update_raises_when_corpus_org_different_to_usr_org(
    client: TestClient, event_service_mock, non_cclw_user_header_token
):
    event_service_mock.org_mismatch = True
    new_data = create_event_write_dto("event1")
    response = client.put(
        "/api/v1/events/E.0.0.1",
        json=jsonable_encoder(new_data),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "Org mismatch"
    assert event_service_mock.update.call_count == 1


def test_update_success_when_corpus_org_different_to_usr_org_super(
    client: TestClient, event_service_mock, superuser_header_token
):
    new_data = create_event_write_dto("event1")
    response = client.put(
        "/api/v1/events/E.0.0.1",
        json=jsonable_encoder(new_data),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "E.0.0.1"
    assert event_service_mock.update.call_count == 1
