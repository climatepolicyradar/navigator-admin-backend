from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.utils import remove_trigger_cols_from_result
from tests.integration_tests.setup_db import EXPECTED_FAMILIES, setup_db

# --- GET


def test_get_family(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A.0.0.1",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "A.0.0.1"

    actual_data = remove_trigger_cols_from_result(data)
    assert actual_data == EXPECTED_FAMILIES[0]


def test_get_family_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A.0.0.1",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_family_when_not_found(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not found: A.0.0.8"


def test_get_family_when_invalid_id(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A008",
        headers=user_header_token,
    )
    assert response.status_code == 400
    data = response.json()
    expected_msg = "The import id A008 is invalid!"
    assert data["detail"] == expected_msg


def test_get_family_when_db_error(
    client: TestClient, data_db: Session, bad_family_repo, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
