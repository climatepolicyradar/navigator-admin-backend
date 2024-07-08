from typing import Tuple, cast

from db_client.models.dfce.family import FamilyDocument, Slug
from db_client.models.document.physical_document import (
    Language,
    LanguageSource,
    PhysicalDocument,
    PhysicalDocumentLanguage,
)
from fastapi import status
from fastapi.testclient import TestClient
from pydantic import AnyHttpUrl
from sqlalchemy.orm import Session

from app.model.document import DocumentWriteDTO
from tests.helpers.document import create_document_write_dto
from tests.integration_tests.setup_db import EXPECTED_DOCUMENTS, setup_db


def _get_doc_tuple(
    test_db: Session, import_id: str
) -> Tuple[FamilyDocument, PhysicalDocument]:
    fd: FamilyDocument = (
        test_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == import_id)
        .one()
    )
    assert fd is not None

    pd: PhysicalDocument = (
        test_db.query(PhysicalDocument)
        .filter(PhysicalDocument.id == fd.physical_document_id)
        .one_or_none()
    )
    assert pd is not None

    return fd, pd


def test_update_document_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    new_document = DocumentWriteDTO(
        variant_name="Translation",
        role="SUMMARY",
        type="Annex",
        metadata={"role": ["SUMMARY"]},
        title="Updated Title",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name="Ghotuo",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.2"
    assert data["variant_name"] == "Translation"
    assert data["role"] == "SUMMARY"
    assert data["metadata"] == {"role": ["SUMMARY"]}
    assert data["type"] == "Annex"
    assert data["title"] == "Updated Title"
    assert data["source_url"] == "http://update_source/"
    assert data["slug"].startswith("updated-title")
    assert data["user_language_name"] == "Ghotuo"

    fd, pd = _get_doc_tuple(data_db, "D.0.0.2")
    assert fd.import_id == "D.0.0.2"
    assert fd.variant_name == "Translation"
    assert fd.document_role == "SUMMARY"
    assert fd.document_type == "Annex"
    assert fd.valid_metadata == {"role": ["SUMMARY"]}
    assert pd.title == "Updated Title"
    assert pd.source_url == "http://update_source/"

    # Check the user language in the db
    lang = (
        data_db.query(PhysicalDocumentLanguage)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one()
    )
    assert lang.language_id == 1

    # Check slug is updated too
    slugs = (
        data_db.query(Slug)
        .filter(Slug.family_document_import_id == "D.0.0.2")
        .order_by(Slug.created.desc())
        .all()
    )
    last_slug = slugs[0].name
    assert last_slug.startswith("updated-title")


def test_update_document_cclw(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    new_document = DocumentWriteDTO(
        variant_name="Translation",
        role="SUMMARY",
        type="Annex",
        metadata={"role": ["SUMMARY"]},
        title="Updated Title",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name="Ghotuo",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.3",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.3"
    assert data["variant_name"] == "Translation"
    assert data["role"] == "SUMMARY"
    assert data["type"] == "Annex"
    assert data["metadata"] == {"role": ["SUMMARY"]}
    assert data["title"] == "Updated Title"
    assert data["source_url"] == "http://update_source/"
    assert data["slug"].startswith("updated-title")
    assert data["user_language_name"] == "Ghotuo"

    fd, pd = _get_doc_tuple(data_db, "D.0.0.3")
    assert fd.import_id == "D.0.0.3"
    assert fd.variant_name == "Translation"
    assert fd.document_role == "SUMMARY"
    assert fd.document_type == "Annex"
    assert fd.valid_metadata == {"role": ["SUMMARY"]}
    assert pd.title == "Updated Title"
    assert pd.source_url == "http://update_source/"

    # Check the user language in the db
    lang = (
        data_db.query(PhysicalDocumentLanguage)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one()
    )
    assert lang.language_id == 1

    # Check slug is updated too
    slugs = (
        data_db.query(Slug)
        .filter(Slug.family_document_import_id == "D.0.0.3")
        .order_by(Slug.created.desc())
        .all()
    )
    last_slug = slugs[0].name
    assert last_slug.startswith("updated-title")


def test_update_document_unfccc(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_document = DocumentWriteDTO(
        variant_name="Translation",
        role="SUMMARY",
        type="Annex",
        metadata={"role": ["SUMMARY"]},
        title="Updated Title",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name="Ghotuo",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.2"
    assert data["variant_name"] == "Translation"
    assert data["role"] == "SUMMARY"
    assert data["metadata"] == {"role": ["SUMMARY"]}
    assert data["type"] == "Annex"
    assert data["title"] == "Updated Title"
    assert data["source_url"] == "http://update_source/"
    assert data["slug"].startswith("updated-title")
    assert data["user_language_name"] == "Ghotuo"

    fd, pd = _get_doc_tuple(data_db, "D.0.0.2")
    assert fd.import_id == "D.0.0.2"
    assert fd.variant_name == "Translation"
    assert fd.document_role == "SUMMARY"
    assert fd.document_type == "Annex"
    assert fd.valid_metadata == {"role": ["SUMMARY"]}
    assert pd.title == "Updated Title"
    assert pd.source_url == "http://update_source/"

    # Check the user language in the db
    lang = (
        data_db.query(PhysicalDocumentLanguage)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one()
    )
    assert lang.language_id == 1

    # Check slug is updated too
    slugs = (
        data_db.query(Slug)
        .filter(Slug.family_document_import_id == "D.0.0.2")
        .order_by(Slug.created.desc())
        .all()
    )
    last_slug = slugs[0].name
    assert last_slug.startswith("updated-title")


def test_update_document_no_source_url(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)

    # Keep all values apart from the Source URL the same.
    new_document = DocumentWriteDTO(
        variant_name="Original Language",
        role="MAIN",
        type="Law",
        metadata={"role": ["MAIN"]},
        title="big title1",
        source_url=None,
        user_language_name="English",
    )

    response = client.put(
        "/api/v1/documents/D.0.0.1",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.1"
    assert data["variant_name"] == "Original Language"
    assert data["role"] == "MAIN"
    assert data["type"] == "Law"
    assert data["title"] == "big title1"
    assert data["source_url"] == new_document.source_url
    assert data["metadata"] == {"role": ["MAIN"]}

    fd, pd = _get_doc_tuple(data_db, "D.0.0.1")
    assert fd.import_id == "D.0.0.1"
    assert fd.variant_name == "Original Language"
    assert fd.document_role == "MAIN"
    assert fd.document_type == "Law"
    assert fd.valid_metadata == {"role": ["MAIN"]}
    assert pd.title == "big title1"
    assert pd.source_url == new_document.source_url

    # Check the user language in the db
    _, lang = (
        data_db.query(PhysicalDocumentLanguage, Language)
        .join(Language, PhysicalDocumentLanguage.language_id == Language.id)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one()
    )
    assert lang.id == 1826
    assert data["user_language_name"] == lang.name


def test_update_document_raises_when_metadata_invalid(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)

    # Keep all values apart from the metadata the same.
    new_document = DocumentWriteDTO(
        variant_name="Original Language",
        role="MAIN",
        type="Law",
        metadata={"color": ["pink"]},
        title="big title1",
        source_url=cast(AnyHttpUrl, "http://source1/"),
        user_language_name="English",
    )

    response = client.put(
        "/api/v1/documents/D.0.0.1",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()

    key_text = "{'role'}"

    expected_message = "Metadata validation failed: "
    expected_missing_message = f"Missing metadata keys: {key_text}"
    expected_extra_message = (
        f"Extra metadata keys: {list(new_document.metadata.keys())}"
    )
    assert data["detail"].startswith(expected_message)
    assert len(data["detail"]) == len(expected_message) + len(
        expected_missing_message
    ) + len(expected_extra_message) + len(",")

    fd, pd = _get_doc_tuple(data_db, "D.0.0.1")
    assert fd.import_id == "D.0.0.1"
    assert fd.variant_name == "Original Language"
    assert fd.document_role == "MAIN"
    assert fd.document_type == "Law"
    assert fd.valid_metadata == {"role": ["MAIN"]}
    assert pd.title == "big title1"
    assert pd.source_url == "http://source1/"


def test_update_document_remove_variant(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)

    # Keep all values apart from the variant the same.
    new_document = DocumentWriteDTO(
        variant_name=None,
        role="MAIN",
        type="Law",
        metadata={"role": ["MAIN"]},
        title="title2",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name=None,
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.2"
    assert data["variant_name"] is None
    assert data["role"] == "MAIN"
    assert data["type"] == "Law"
    assert data["title"] == "title2"
    assert data["source_url"] == "http://update_source/"

    fd, pd = _get_doc_tuple(data_db, "D.0.0.2")
    assert fd.import_id == "D.0.0.2"
    assert fd.variant_name is None
    assert fd.document_role == "MAIN"
    assert fd.document_type == "Law"
    assert pd.title == "title2"
    assert pd.source_url == "http://update_source/"

    # Check the user language in the db
    lang = (
        data_db.query(PhysicalDocumentLanguage, Language)
        .join(Language, PhysicalDocumentLanguage.language_id == Language.id)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one_or_none()
    )
    assert lang is None


def test_update_document_remove_user_language(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)

    # Keep all values apart from the language the same as in setup_db.py.
    new_document = DocumentWriteDTO(
        variant_name="Original Language",
        role="MAIN",
        type="Law",
        metadata={"role": ["MAIN"]},
        title="big title1",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name=None,
    )
    response = client.put(
        "/api/v1/documents/D.0.0.1",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.1"
    assert data["variant_name"] == "Original Language"
    assert data["role"] == "MAIN"
    assert data["type"] == "Law"
    assert data["title"] == "big title1"
    assert data["source_url"] == "http://update_source/"
    assert data["metadata"] == {"role": ["MAIN"]}

    fd, pd = _get_doc_tuple(data_db, "D.0.0.1")
    assert fd.import_id == "D.0.0.1"
    assert fd.variant_name == "Original Language"
    assert fd.document_role == "MAIN"
    assert fd.document_type == "Law"
    assert fd.valid_metadata == {"role": ["MAIN"]}
    assert pd.title == "big title1"

    # Check the user language in the db
    lang = (
        data_db.query(PhysicalDocumentLanguage, Language)
        .join(Language, PhysicalDocumentLanguage.language_id == Language.id)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one_or_none()
    )
    assert lang is None
    assert data["user_language_name"] is None


def test_update_document_when_not_authorised(client: TestClient, data_db: Session):
    setup_db(data_db)
    new_document = create_document_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2", json=new_document.model_dump(mode="json")
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_document_idempotent(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    doc = EXPECTED_DOCUMENTS[0]
    document = {
        "variant_name": doc["variant_name"],
        "role": doc["role"],
        "type": doc["type"],
        "metadata": doc["metadata"],
        "title": doc["title"],
        "source_url": doc["source_url"],
        "user_language_name": doc["user_language_name"],
    }

    response = client.put(
        f"/api/v1/documents/{doc['import_id']}",
        json=document,
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["title"] == EXPECTED_DOCUMENTS[0]["title"]

    _, pd = _get_doc_tuple(data_db, EXPECTED_DOCUMENTS[0]["import_id"])
    assert pd.title == EXPECTED_DOCUMENTS[0]["title"]


def test_update_document_rollback(
    client: TestClient,
    data_db: Session,
    rollback_document_repo,
    non_cclw_user_header_token,
):
    setup_db(data_db)
    new_document = create_document_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    _, pd = _get_doc_tuple(data_db, "D.0.0.2")
    assert pd.title != "Updated Title"

    assert rollback_document_repo.update.call_count == 1


def test_update_document_when_not_found(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_document = create_document_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.22",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Document not updated: D.0.0.22"


def test_update_document_when_db_error(
    client: TestClient, data_db: Session, bad_document_repo, non_cclw_user_header_token
):
    setup_db(data_db)

    new_document = create_document_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_update_document_blank_variant(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_document = DocumentWriteDTO(
        variant_name="",
        role="SUMMARY",
        type="Annex",
        metadata={"role": ["SUMMARY"]},
        title="Updated Title",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name="Ghotuo",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Variant name is empty"


def test_update_document_idempotent_user_language(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_document = DocumentWriteDTO(
        variant_name="Original Language",
        role="MAIN",
        type="Law",
        metadata={"role": ["MAIN"]},
        title="title2",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name=None,
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.2"
    assert data["variant_name"] == "Original Language"
    assert data["role"] == "MAIN"
    assert data["type"] == "Law"
    assert data["title"] == "title2"
    assert data["source_url"] == "http://update_source/"
    assert data["metadata"] == {"role": ["MAIN"]}

    fd, pd = _get_doc_tuple(data_db, "D.0.0.2")
    assert fd.import_id == "D.0.0.2"
    assert fd.variant_name == "Original Language"
    assert fd.document_role == "MAIN"
    assert fd.document_type == "Law"
    assert fd.valid_metadata == {"role": ["MAIN"]}
    assert pd.title == "title2"
    assert pd.source_url == "http://update_source/"

    # Check the user language in the db
    lang = (
        data_db.query(PhysicalDocumentLanguage, Language)
        .join(Language, PhysicalDocumentLanguage.language_id == Language.id)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one_or_none()
    )
    assert lang is None
    assert data["user_language_name"] is None


def test_update_document_when_org_mismatch(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)

    new_document = create_document_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"]
        == "User 'cclw@cpr.org' is not authorised to perform operation on 'D.0.0.2'"
    )
