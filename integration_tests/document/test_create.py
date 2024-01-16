from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.clients.db.models.document import PhysicalDocument
from app.clients.db.models.document.physical_document import PhysicalDocumentLanguage
from app.clients.db.models.law_policy import FamilyDocument
from app.clients.db.models.law_policy.family import DocumentStatus, Slug
from integration_tests.setup_db import setup_db
from unit_tests.helpers.document import create_document_create_dto


def test_create_document(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_fd = (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )

    assert actual_fd is not None
    assert actual_fd.variant_name is not None

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


def test_create_document_null_variant(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = create_document_create_dto(
        title="Title", family_import_id="A.0.0.3", variant_name=None
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_fd = (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )

    assert actual_fd is not None
    assert actual_fd.variant_name is None

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


def test_create_document_null_user_language_name(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = create_document_create_dto(
        title="Title", family_import_id="A.0.0.3", user_language_name=None
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED

    created_import_id = response.json()
    actual_fd = (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )
    assert actual_fd is not None

    language = (
        test_db.query(PhysicalDocumentLanguage)
        .filter(PhysicalDocumentLanguage.document_id == actual_fd.physical_document_id)
        .one_or_none()
    )
    assert language is None

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
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_document_rollback(
    client: TestClient, test_db: Session, rollback_document_repo, user_header_token
):
    setup_db(test_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
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
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
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
    new_document = create_document_create_dto(title="Title", family_import_id="invalid")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "The import id invalid is invalid!"


def test_create_document_when_family_missing(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = create_document_create_dto(
        title="Title",
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert (
        data["detail"] == f"Could not find family for {new_document.family_import_id}"
    )


def test_create_document_when_empty_variant(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = create_document_create_dto(title="Empty variant", variant_name="")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Variant name is empty"


def test_create_document_when_invalid_variant(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = create_document_create_dto(
        title="Title", family_import_id="A.0.0.3", variant_name="Invalid"
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert '(Invalid) is not present in table "variant"' in data["detail"]


def test_document_status_is_published_on_create(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_fd = (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )

    assert actual_fd is not None
    assert actual_fd.document_status is DocumentStatus.CREATED
