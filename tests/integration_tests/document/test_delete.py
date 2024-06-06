from db_client.models.dfce import FamilyDocument
from db_client.models.dfce.family import DocumentStatus
from db_client.models.document import PhysicalDocument
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db


def test_delete_document_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/documents/D.0.0.2", headers=superuser_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    assert data_db.query(FamilyDocument).count() == 3
    assert (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "D.0.0.2")
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 1
    )
    assert data_db.query(PhysicalDocument).count() == 3


def test_delete_document_cclw(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.delete("/api/v1/documents/D.0.0.3", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert data_db.query(FamilyDocument).count() == 3
    assert (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "D.0.0.3")
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 1
    )
    assert data_db.query(PhysicalDocument).count() == 3


def test_delete_document_unfccc(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/documents/D.0.0.2", headers=non_cclw_user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    assert data_db.query(FamilyDocument).count() == 3
    assert (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "D.0.0.2")
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 1
    )
    assert data_db.query(PhysicalDocument).count() == 3


def test_delete_document_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/documents/D.0.0.2",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert data_db.query(FamilyDocument).count() == 3
    assert (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 0
    )
    assert data_db.query(PhysicalDocument).count() == 3


def test_delete_document_rollback(
    client: TestClient,
    data_db: Session,
    rollback_document_repo,
    user_header_token,
):
    setup_db(data_db)
    response = client.delete("/api/v1/documents/D.0.0.3", headers=user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert data_db.query(FamilyDocument).count() == 3
    assert (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 0
    )
    assert data_db.query(PhysicalDocument).count() == 3
    assert rollback_document_repo.delete.call_count == 1


def test_delete_document_when_not_found(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.delete("/api/v1/documents/D.0.0.22", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Document D.0.0.22 does not exist"
    assert data_db.query(FamilyDocument).count() == 3
    assert (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 0
    )
    assert data_db.query(PhysicalDocument).count() == 3


def test_delete_document_when_db_error(
    client: TestClient, data_db: Session, bad_document_repo, user_header_token
):
    setup_db(data_db)
    response = client.delete("/api/v1/documents/D.0.0.1", headers=user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_delete_document_when_org_mismatch(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.delete("/api/v1/documents/D.0.0.2", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert data_db.query(FamilyDocument).count() == 3
    assert (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 0
    )
    assert data_db.query(PhysicalDocument).count() == 3
