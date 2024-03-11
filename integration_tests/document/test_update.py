from typing import Tuple, cast

from db_client.models.document.physical_document import (
    LanguageSource,
    PhysicalDocument,
    PhysicalDocumentLanguage,
)
from db_client.models.law_policy.family import FamilyDocument, Slug
from fastapi import status
from fastapi.testclient import TestClient
from pydantic import AnyHttpUrl
from sqlalchemy.orm import Session

from app.model.document import DocumentWriteDTO
from integration_tests.setup_db import EXPECTED_DOCUMENTS, setup_db
from unit_tests.helpers.document import create_document_write_dto


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


def test_update_document(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    new_document = DocumentWriteDTO(
        variant_name="Translation",
        role="SUMMARY",
        type="Annex",
        title="Updated Title",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name="Ghotuo",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.2"
    assert data["variant_name"] == "Translation"
    assert data["role"] == "SUMMARY"
    assert data["type"] == "Annex"
    assert data["title"] == "Updated Title"
    assert data["source_url"] == "http://update_source/"
    assert data["slug"].startswith("updated-title")
    assert data["user_language_name"] == "Ghotuo"

    fd, pd = _get_doc_tuple(test_db, "D.0.0.2")
    assert fd.import_id == "D.0.0.2"
    assert fd.variant_name == "Translation"
    assert fd.document_role == "SUMMARY"
    assert fd.document_type == "Annex"
    assert pd.title == "Updated Title"
    assert pd.source_url == "http://update_source/"

    # Check the user language in the db
    lang = (
        test_db.query(PhysicalDocumentLanguage)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one()
    )
    assert lang.language_id == 1

    # Check slug is updated too
    slugs = (
        test_db.query(Slug).filter(Slug.family_document_import_id == "D.0.0.2").all()
    )
    last_slug = slugs[-1].name
    assert last_slug.startswith("updated-title")


def test_update_document_no_source_url(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = DocumentWriteDTO(
        variant_name="Translation",
        role="SUMMARY",
        type="Annex",
        title="Updated Title No Source URL",
        source_url=None,
        user_language_name="Ghotuo",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.2"
    assert data["variant_name"] == "Translation"
    assert data["role"] == "SUMMARY"
    assert data["type"] == "Annex"
    assert data["title"] == new_document.title
    assert data["source_url"] == new_document.source_url
    assert data["slug"].startswith("updated-title")
    assert data["user_language_name"] == "Ghotuo"

    fd, pd = _get_doc_tuple(test_db, "D.0.0.2")
    assert fd.import_id == "D.0.0.2"
    assert fd.variant_name == "Translation"
    assert fd.document_role == "SUMMARY"
    assert fd.document_type == "Annex"
    assert pd.title == new_document.title
    assert pd.source_url == new_document.source_url

    # Check the user language in the db
    lang = (
        test_db.query(PhysicalDocumentLanguage)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one()
    )
    assert lang.language_id == 1

    # Check slug is updated too
    slugs = (
        test_db.query(Slug).filter(Slug.family_document_import_id == "D.0.0.2").all()
    )
    last_slug = slugs[-1].name
    assert last_slug.startswith("updated-title")


def test_update_document_remove_variant(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = DocumentWriteDTO(
        variant_name=None,
        role="SUMMARY",
        type="Annex",
        title="Updated Title",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name="Ghotuo",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.2"
    assert data["variant_name"] is None
    assert data["role"] == "SUMMARY"
    assert data["type"] == "Annex"
    assert data["title"] == "Updated Title"
    assert data["source_url"] == "http://update_source/"
    assert data["slug"].startswith("updated-title")
    assert data["user_language_name"] == "Ghotuo"

    fd, pd = _get_doc_tuple(test_db, "D.0.0.2")
    assert fd.import_id == "D.0.0.2"
    assert fd.variant_name is None
    assert fd.document_role == "SUMMARY"
    assert fd.document_type == "Annex"
    assert pd.title == "Updated Title"
    assert pd.source_url == "http://update_source/"

    # Check the user language in the db
    lang = (
        test_db.query(PhysicalDocumentLanguage)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one()
    )
    assert lang.language_id == 1

    # Check slug is updated too
    slugs = (
        test_db.query(Slug).filter(Slug.family_document_import_id == "D.0.0.2").all()
    )
    last_slug = slugs[-1].name
    assert last_slug.startswith("updated-title")


def test_update_document_remove_user_language(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = DocumentWriteDTO(
        variant_name=None,
        role="SUMMARY",
        type="Annex",
        title="Updated Title",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name=None,
    )
    response = client.put(
        "/api/v1/documents/D.0.0.1",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.1"
    assert data["variant_name"] is None
    assert data["role"] == "SUMMARY"
    assert data["type"] == "Annex"
    assert data["title"] == "Updated Title"
    assert data["source_url"] == "http://update_source/"
    assert data["slug"].startswith("updated-title")
    assert data["user_language_name"] is None

    fd, pd = _get_doc_tuple(test_db, "D.0.0.1")
    assert fd.import_id == "D.0.0.1"
    assert fd.variant_name is None
    assert fd.document_role == "SUMMARY"
    assert fd.document_type == "Annex"
    assert pd.title == "Updated Title"
    assert pd.source_url == "http://update_source/"

    # Check the user language in the db
    lang = (
        test_db.query(PhysicalDocumentLanguage)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one_or_none()
    )
    assert lang is None

    # Check slug is updated too
    slugs = (
        test_db.query(Slug).filter(Slug.family_document_import_id == "D.0.0.1").all()
    )
    last_slug = slugs[-1].name
    assert last_slug.startswith("updated-title")


def test_update_document_when_not_authorised(client: TestClient, test_db: Session):
    setup_db(test_db)
    new_document = create_document_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2", json=new_document.model_dump(mode="json")
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_document_idempotent(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    doc = EXPECTED_DOCUMENTS[0]
    document = {
        "variant_name": doc["variant_name"],
        "role": doc["role"],
        "type": doc["type"],
        "title": doc["title"],
        "source_url": doc["source_url"],
        "user_language_name": doc["user_language_name"],
    }

    response = client.put(
        f"/api/v1/documents/{doc['import_id']}",
        json=document,
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["title"] == EXPECTED_DOCUMENTS[0]["title"]

    _, pd = _get_doc_tuple(test_db, EXPECTED_DOCUMENTS[0]["import_id"])
    assert pd.title == EXPECTED_DOCUMENTS[0]["title"]


def test_update_document_rollback(
    client: TestClient, test_db: Session, rollback_document_repo, user_header_token
):
    setup_db(test_db)
    new_document = create_document_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    _, pd = _get_doc_tuple(test_db, "D.0.0.2")
    assert pd.title != "Updated Title"

    assert rollback_document_repo.update.call_count == 1


def test_update_document_when_not_found(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
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
    client: TestClient, test_db: Session, bad_document_repo, user_header_token
):
    setup_db(test_db)

    new_document = create_document_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_document_repo.update.call_count == 1


def test_update_document_blank_variant(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = DocumentWriteDTO(
        variant_name="",
        role="SUMMARY",
        type="Annex",
        title="Updated Title",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name="Ghotuo",
    )
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Variant name is empty"


def test_update_document_idempotent_user_language(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_document = DocumentWriteDTO(
        variant_name="Translation",
        role="SUMMARY",
        type="Annex",
        title="Updated Title",
        source_url=cast(AnyHttpUrl, "http://update_source"),
        user_language_name=None,
    )
    print(new_document.model_dump(mode="json"))
    response = client.put(
        "/api/v1/documents/D.0.0.2",
        json=new_document.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "D.0.0.2"
    assert data["variant_name"] == "Translation"
    assert data["role"] == "SUMMARY"
    assert data["type"] == "Annex"
    assert data["title"] == "Updated Title"
    assert data["source_url"] == "http://update_source/"
    assert data["slug"].startswith("updated-title")
    assert data["user_language_name"] is None

    fd, pd = _get_doc_tuple(test_db, "D.0.0.2")
    assert fd.import_id == "D.0.0.2"
    assert fd.variant_name == "Translation"
    assert fd.document_role == "SUMMARY"
    assert fd.document_type == "Annex"
    assert pd.title == "Updated Title"
    assert pd.source_url == "http://update_source/"

    # Check the user language in the db
    lang = (
        test_db.query(PhysicalDocumentLanguage)
        .filter(PhysicalDocumentLanguage.document_id == data["physical_id"])
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one_or_none()
    )
    assert lang is None

    # Check slug is updated too
    slugs = (
        test_db.query(Slug).filter(Slug.family_document_import_id == "D.0.0.2").all()
    )
    last_slug = slugs[-1].name
    assert last_slug.startswith("updated-title")
