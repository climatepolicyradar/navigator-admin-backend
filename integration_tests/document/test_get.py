from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from integration_tests.setup_db import EXPECTED_DOCUMENTS, setup_db

# --- GET ALL


def test_get_all_documents(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["D.0.0.1", "D.0.0.2"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    sdata = sorted(data, key=lambda d: d["import_id"])
    assert all(field in col for col in sdata for field in ("created", "last_modified"))

    expected_data = [
        {k: v for k, v in col.items() if k not in ("created", "last_modified")}
        for col in sdata
    ]
    assert expected_data[0] == EXPECTED_DOCUMENTS[0]
    assert expected_data[1] == EXPECTED_DOCUMENTS[1]


def test_get_all_documents_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- GET


def test_get_document(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/D.0.0.1",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.1"

    assert all(field in data for field in ("created", "last_modified"))
    expected_data = {
        k: v for k, v in data.items() if k not in ("created", "last_modified")
    }
    assert expected_data == EXPECTED_DOCUMENTS[0]


def test_get_document_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/D.0.0.1",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_document_when_not_found(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/D.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Document not found: D.0.0.8"


def test_get_document_when_id_invalid(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/A008",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    expected_msg = "The import id A008 is invalid!"
    assert data["detail"] == expected_msg


def test_get_document_when_db_error(
    client: TestClient, data_db: Session, bad_document_repo, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents/A.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
