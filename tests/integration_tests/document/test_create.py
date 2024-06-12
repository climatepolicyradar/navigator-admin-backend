from db_client.models.dfce import FamilyDocument
from db_client.models.dfce.family import DocumentStatus, Slug
from db_client.models.document import PhysicalDocument
from db_client.models.document.physical_document import PhysicalDocumentLanguage
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.document import create_document_create_dto
from tests.integration_tests.setup_db import setup_db

SLUG_HASH = 4
SLUG_SEPARATOR = 1


def test_create_document_cclw(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.2")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_fd = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )

    assert actual_fd is not None
    assert actual_fd.variant_name is not None

    actual_pd = (
        data_db.query(PhysicalDocument)
        .filter(PhysicalDocument.id == actual_fd.physical_document_id)
        .one()
    )
    assert actual_pd is not None
    assert actual_pd.title == "Title"

    slug = (
        data_db.query(Slug)
        .filter(Slug.family_document_import_id == actual_fd.import_id)
        .one()
    )
    assert len(slug.name) == len("title") + SLUG_SEPARATOR + SLUG_HASH
    assert slug.name.startswith("title")


def test_create_document_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_fd = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )

    assert actual_fd is not None
    assert actual_fd.variant_name is not None

    actual_pd = (
        data_db.query(PhysicalDocument)
        .filter(PhysicalDocument.id == actual_fd.physical_document_id)
        .one()
    )
    assert actual_pd is not None
    assert actual_pd.title == "Title"

    slug = (
        data_db.query(Slug)
        .filter(Slug.family_document_import_id == actual_fd.import_id)
        .one()
    )
    assert len(slug.name) == len("title") + SLUG_SEPARATOR + SLUG_HASH
    assert slug.name.startswith("title")


def test_create_document_unfccc(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_fd = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )

    assert actual_fd is not None
    assert actual_fd.variant_name is not None

    actual_pd = (
        data_db.query(PhysicalDocument)
        .filter(PhysicalDocument.id == actual_fd.physical_document_id)
        .one()
    )
    assert actual_pd is not None
    assert actual_pd.title == "Title"

    slug = (
        data_db.query(Slug)
        .filter(Slug.family_document_import_id == actual_fd.import_id)
        .one()
    )
    assert len(slug.name) == len("title") + SLUG_SEPARATOR + SLUG_HASH
    assert slug.name.startswith("title")


def test_create_document_null_variant(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(
        title="Title", family_import_id="A.0.0.3", variant_name=None
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_fd = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )

    assert actual_fd is not None
    assert actual_fd.variant_name is None

    actual_pd = (
        data_db.query(PhysicalDocument)
        .filter(PhysicalDocument.id == actual_fd.physical_document_id)
        .one()
    )
    assert actual_pd is not None
    assert actual_pd.title == "Title"

    slug = (
        data_db.query(Slug)
        .filter(Slug.family_document_import_id == actual_fd.import_id)
        .one()
    )
    assert len(slug.name) == len("title") + SLUG_SEPARATOR + SLUG_HASH
    assert slug.name.startswith("title")


def test_create_document_null_user_language_name(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(
        title="Title", family_import_id="A.0.0.3", user_language_name=None
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED

    created_import_id = response.json()
    actual_fd = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )
    assert actual_fd is not None

    language = (
        data_db.query(PhysicalDocumentLanguage)
        .filter(PhysicalDocumentLanguage.document_id == actual_fd.physical_document_id)
        .one_or_none()
    )
    assert language is None

    actual_pd = (
        data_db.query(PhysicalDocument)
        .filter(PhysicalDocument.id == actual_fd.physical_document_id)
        .one()
    )
    assert actual_pd is not None
    assert actual_pd.title == "Title"

    slug = (
        data_db.query(Slug)
        .filter(Slug.family_document_import_id == actual_fd.import_id)
        .one()
    )
    assert len(slug.name) == len("title") + SLUG_SEPARATOR + SLUG_HASH
    assert slug.name.startswith("title")


def test_create_document_null_source_url(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(
        title="Title", family_import_id="A.0.0.3", source_url=None
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_fd = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )

    assert actual_fd is not None

    actual_pd = (
        data_db.query(PhysicalDocument)
        .filter(PhysicalDocument.id == actual_fd.physical_document_id)
        .one()
    )
    assert actual_pd is not None
    assert actual_pd.source_url is None

    slug = (
        data_db.query(Slug)
        .filter(Slug.family_document_import_id == actual_fd.import_id)
        .one()
    )
    assert len(slug.name) == len("title") + SLUG_SEPARATOR + SLUG_HASH
    assert slug.name.startswith("title")


def test_create_document_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_document_rollback(
    client: TestClient,
    data_db: Session,
    rollback_document_repo,
    non_cclw_user_header_token,
):
    setup_db(data_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    actual_fd = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "A.0.0.9")
        .one_or_none()
    )
    assert actual_fd is None
    assert rollback_document_repo.create.call_count == 1


def test_create_document_when_db_error(
    client: TestClient, data_db: Session, bad_document_repo, non_cclw_user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_document_repo.create.call_count == 1


def test_create_document_when_family_invalid(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(title="Title", family_import_id="invalid")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "The import id invalid is invalid!"


def test_create_document_when_family_missing(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(
        title="Title",
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert (
        data["detail"] == f"Could not find family for {new_document.family_import_id}"
    )


def test_create_document_when_empty_variant(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(title="Empty variant", variant_name="")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Variant name is empty"


def test_create_document_when_invalid_variant(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(
        title="Title", family_import_id="A.0.0.2", variant_name="Invalid"
    )
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert "app.service.document::create" in data["detail"]


def test_document_status_is_created_on_create(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.2")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_fd = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == created_import_id)
        .one()
    )

    assert actual_fd is not None
    assert actual_fd.document_status is DocumentStatus.CREATED


def test_create_document_when_org_mismatch(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_document = create_document_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/documents",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
