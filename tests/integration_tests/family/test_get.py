from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import EXPECTED_FAMILIES, setup_db

# --- GET ALL


def test_get_all_families_superuser(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["A.0.0.1", "A.0.0.2", "A.0.0.3"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    assert all(field in fam for fam in data for field in ("created", "last_modified"))
    sorted_data = sorted(data, key=lambda d: d["import_id"])
    response_data = [
        {
            k: v if not isinstance(v, list) else sorted(v)
            for k, v in fam.items()
            if k not in ("created", "last_modified")
        }
        for fam in sorted_data
    ]
    assert response_data[0] == EXPECTED_FAMILIES[0]
    assert response_data[1] == EXPECTED_FAMILIES[1]
    assert response_data[2] == EXPECTED_FAMILIES[2]


def test_get_all_families_cclw(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["A.0.0.1", "A.0.0.2"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    assert all(field in fam for fam in data for field in ("created", "last_modified"))
    sorted_data = sorted(data, key=lambda d: d["import_id"])
    response_data = [
        {
            k: v if not isinstance(v, list) else sorted(v)
            for k, v in fam.items()
            if k not in ("created", "last_modified")
        }
        for fam in sorted_data
    ]
    assert response_data[0] == EXPECTED_FAMILIES[0]
    assert response_data[1] == EXPECTED_FAMILIES[1]


def test_get_all_families_unfccc(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families",
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["A.0.0.3"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    assert all(field in fam for fam in data for field in ("created", "last_modified"))
    sorted_data = sorted(data, key=lambda d: d["import_id"])
    response_data = [
        {
            k: v if not isinstance(v, list) else sorted(v)
            for k, v in fam.items()
            if k not in ("created", "last_modified")
        }
        for fam in sorted_data
    ]
    assert response_data[0] == EXPECTED_FAMILIES[2]


def test_get_all_families_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


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

    assert all(field in data for field in ("created", "last_modified"))
    expected_data = {
        k: v for k, v in data.items() if k not in ("created", "last_modified")
    }
    assert expected_data == EXPECTED_FAMILIES[0]


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
