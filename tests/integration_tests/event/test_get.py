from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import EXPECTED_EVENTS, setup_db

# --- GET ALL


def test_get_all_events(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["E.0.0.1", "E.0.0.2", "E.0.0.3"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    assert all(
        field in event for event in data for field in ("created", "last_modified")
    )
    data = sorted(data, key=lambda d: d["import_id"])
    expected_data = [
        {
            k: v if not isinstance(v, list) else sorted(v)
            for k, v in event.items()
            if k not in ("created", "last_modified")
        }
        for event in data
    ]
    assert expected_data[0] == EXPECTED_EVENTS[0]
    assert expected_data[1] == EXPECTED_EVENTS[1]
    assert expected_data[2] == EXPECTED_EVENTS[2]


def test_get_all_events_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- GET


def test_get_event(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events/E.0.0.1",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "E.0.0.1"

    assert all(field in data for field in ("created", "last_modified"))
    expected_data = {
        k: v for k, v in data.items() if k not in ("created", "last_modified")
    }
    assert expected_data == EXPECTED_EVENTS[0]


def test_get_event_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events/E.0.0.1",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_event_when_not_found(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events/E.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Event not found: E.0.0.8"


def test_get_event_when_id_invalid(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events/E008",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    expected_msg = "The import id E008 is invalid!"
    assert data["detail"] == expected_msg


def test_get_event_when_db_error(
    client: TestClient, data_db: Session, bad_event_repo, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events/A.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
