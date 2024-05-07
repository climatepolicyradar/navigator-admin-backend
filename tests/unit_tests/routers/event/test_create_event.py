from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from tests.helpers.event import create_event_create_dto


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
