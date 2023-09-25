from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from app.clients.db.models.law_policy import FamilyDocument
from app.clients.db.models.document import PhysicalDocument
from app.clients.db.models.law_policy.family import Slug
from integration_tests.setup_db import setup_db
from unit_tests.helpers.document import create_document_write_dto


def test_create_document(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    new_document = create_document_write_dto(
        import_id="D.0.0.9",
        family_import_id="A.0.0.1",
        title="Title",
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Title"

    actual_fd = (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "D.0.0.9")
        .one()
    )
    assert actual_fd is not None

    actual_pd = (
        test_db.query(PhysicalDocument)
        .filter(PhysicalDocument.id == actual_fd.physical_document_id)
        .one()
    )
    assert actual_pd is not None
    assert actual_pd.title == "Title"

    slug = (
        test_db.query(Slug)
        .filter(Slug.family_document_import_id == actual_fd.import_id)
        .one()
    )
    assert len(slug.name) == len("title") + 1 + 4
    assert slug.name.startswith("title")


def test_create_document_when_not_authenticated(client: TestClient, test_db: Session):
    setup_db(test_db)
    new_document = create_document_write_dto(
        import_id="A.0.0.9",
        family_import_id="A.0.0.1",
        title="Title",
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_document_rollback(
    client: TestClient, test_db: Session, rollback_document_repo, user_header_token
):
    setup_db(test_db)
    new_document = create_document_write_dto(
        import_id="A.0.0.9",
        family_import_id="A.0.0.1",
        title="Title",
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    actual_fd = (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "A.0.0.9")
        .one_or_none()
    )
    assert actual_fd is None
    assert rollback_document_repo.create.call_count == 1


def test_create_document_when_db_error(
    client: TestClient, test_db: Session, bad_document_repo, user_header_token
):
    setup_db(test_db)
    new_document = create_document_write_dto(
        import_id="A.0.0.9",
        family_import_id="A.0.0.1",
        title="Title",
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_document_repo.create.call_count == 1


def test_create_document_when_family_invalid(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = create_document_write_dto(
        import_id="A.0.0.9",
        family_import_id="A.0.100",
        title="Title",
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "The import id A.0.100 is invalid!"


def test_create_document_when_family_missing(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = create_document_write_dto(
        import_id="A.0.0.9",
        family_import_id="A.0.0.100",
        title="Title",
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
