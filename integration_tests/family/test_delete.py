from db_client.models.dfce import DocumentStatus, Family, FamilyDocument, FamilyStatus
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from integration_tests.setup_db import setup_db


def test_delete_family(client: TestClient, data_db: Session, admin_user_header_token):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/families/A.0.0.3", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    assert data_db.query(Family).count() == 3
    assert (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 2
    )
    family = data_db.query(Family).filter(Family.import_id == "A.0.0.3").all()
    assert len(family) == 1
    assert family[0].family_status == FamilyStatus.DELETED


def test_delete_family_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/families/A.0.0.2",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_family_rollback(
    client: TestClient, data_db: Session, rollback_family_repo, admin_user_header_token
):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/families/A.0.0.3", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 0
    )
    test_family = data_db.query(Family).filter(Family.import_id == "A.0.0.3").one()
    assert test_family.family_status != FamilyStatus.DELETED


def test_delete_family_when_not_found(
    client: TestClient, data_db: Session, admin_user_header_token
):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/families/A.0.0.22", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not deleted: A.0.0.22"


def test_delete_family_when_db_error(
    client: TestClient, data_db: Session, bad_family_repo, admin_user_header_token
):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/families/A.0.0.1", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
