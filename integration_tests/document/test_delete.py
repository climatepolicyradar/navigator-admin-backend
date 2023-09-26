from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from app.clients.db.models.law_policy import FamilyDocument
from app.clients.db.models.document import PhysicalDocument
from app.clients.db.models.law_policy.family import DocumentStatus
from integration_tests.setup_db import setup_db
import app.repository.document as document_repo


def test_delete_document(client: TestClient, test_db: Session, admin_user_header_token):
    setup_db(test_db)
    response = client.delete(
        "/api/v1/documents/D.0.0.2", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    assert test_db.query(FamilyDocument).count() == 2
    assert (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 1
    )
    assert test_db.query(PhysicalDocument).count() == 2


def test_delete_document_when_not_authenticated(
    client: TestClient, test_db: Session, mocker
):
    setup_db(test_db)
    mocker.spy(document_repo, "delete")
    response = client.delete(
        "/api/v1/documents/D.0.0.2",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert test_db.query(FamilyDocument).count() == 2
    assert (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 0
    )
    assert test_db.query(PhysicalDocument).count() == 2
    assert document_repo.delete.call_count == 0


def test_delete_document_rollback(
    client: TestClient,
    test_db: Session,
    rollback_document_repo,
    admin_user_header_token,
):
    setup_db(test_db)
    response = client.delete(
        "/api/v1/documents/D.0.0.2", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert test_db.query(FamilyDocument).count() == 2
    assert (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 0
    )
    assert test_db.query(PhysicalDocument).count() == 2
    assert rollback_document_repo.delete.call_count == 1


def test_delete_document_when_not_found(
    client: TestClient, test_db: Session, admin_user_header_token
):
    setup_db(test_db)
    response = client.delete(
        "/api/v1/documents/D.0.0.22", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Document not deleted: D.0.0.22"
    assert test_db.query(FamilyDocument).count() == 2
    assert (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.document_status == DocumentStatus.DELETED)
        .count()
        == 0
    )
    assert test_db.query(PhysicalDocument).count() == 2


def test_delete_document_when_db_error(
    client: TestClient, test_db: Session, bad_document_repo, admin_user_header_token
):
    setup_db(test_db)
    response = client.delete(
        "/api/v1/documents/D.0.0.1", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_document_repo.delete.call_count == 1
