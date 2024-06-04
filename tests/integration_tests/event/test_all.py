from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.utils import remove_trigger_cols_from_result
from tests.integration_tests.setup_db import EXPECTED_EVENTS, setup_db

# --- GET ALL


def test_get_all_events_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["E.0.0.1", "E.0.0.2", "E.0.0.3"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    actual_data = remove_trigger_cols_from_result(data)
    assert actual_data is not None
    assert actual_data[0] == EXPECTED_EVENTS[0]
    assert actual_data[1] == EXPECTED_EVENTS[1]
    assert actual_data[2] == EXPECTED_EVENTS[2]


def test_get_all_events_cclw(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["E.0.0.1", "E.0.0.2"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    actual_data = remove_trigger_cols_from_result(data)
    assert actual_data is not None
    assert actual_data[0] == EXPECTED_EVENTS[0]
    assert actual_data[1] == EXPECTED_EVENTS[1]


def test_get_all_events_unfccc(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events",
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["E.0.0.3"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    actual_data = remove_trigger_cols_from_result(data)
    assert actual_data is not None
    assert actual_data[0] == EXPECTED_EVENTS[2]


def test_get_all_events_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/events",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
