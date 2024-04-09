from db_client.models.dfce.collection import Collection
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import EXPECTED_NUM_COLLECTIONS, setup_db


def test_delete_collection(
    client: TestClient, data_db: Session, admin_user_header_token
):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/collections/C.0.0.2", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    n = data_db.query(Collection).count()
    assert n == EXPECTED_NUM_COLLECTIONS - 1


def test_delete_collection_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/collections/C.0.0.2",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_collection_rollback(
    client: TestClient,
    data_db: Session,
    rollback_collection_repo,
    admin_user_header_token,
):
    setup_db(data_db)
    n = data_db.query(Collection).count()
    assert n == EXPECTED_NUM_COLLECTIONS
    response = client.delete(
        "/api/v1/collections/C.0.0.2", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    n = data_db.query(Collection).count()
    assert n == EXPECTED_NUM_COLLECTIONS
    assert rollback_collection_repo.delete.call_count == 1


def test_delete_collection_when_not_found(
    client: TestClient, data_db: Session, admin_user_header_token
):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/collections/C.0.0.22", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not deleted: C.0.0.22"
    n = data_db.query(Collection).count()
    assert n == EXPECTED_NUM_COLLECTIONS


def test_delete_collection_when_db_error(
    client: TestClient, data_db: Session, bad_collection_repo, admin_user_header_token
):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/collections/C.0.0.1", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_collection_repo.delete.call_count == 1
