import logging

import pytest
from db_client.models.dfce import FamilyEvent
from db_client.models.dfce.collection import Collection, CollectionFamily
from db_client.models.dfce.family import Family, FamilyDocument
from db_client.models.dfce.metadata import FamilyMetadata
from db_client.models.document.physical_document import (
    Language,
    PhysicalDocument,
    PhysicalDocumentLanguage,
)
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.model.corpus import CorpusCreateDTO
from app.model.corpus_type import CorpusTypeCreateDTO
from app.repository import corpus as corpus_repo
from app.repository import corpus_type as corpus_type_repo
from app.service.bulk_import import DEFAULT_DOCUMENT_LIMIT
from tests.helpers.bulk_import import (
    build_json_file,
    default_collection,
    default_document,
    default_event,
    default_family,
)


def create_input_json_with_two_of_each_entity():
    return build_json_file(
        {
            "collections": [
                default_collection,
                {**default_collection, "import_id": "test.new.collection.1"},
            ],
            "families": [
                default_family,
                {
                    **default_family,
                    "import_id": "test.new.family.1",
                    "collections": ["test.new.collection.1"],
                },
            ],
            "documents": [
                default_document,
                {
                    **default_document,
                    "import_id": "test.new.document.1",
                    "family_import_id": "test.new.family.1",
                },
            ],
            "events": [
                default_event,
                {
                    **default_event,
                    "import_id": "test.new.event.1",
                    "family_import_id": "test.new.family.1",
                },
            ],
        }
    )


@pytest.mark.s3
def test_bulk_import_successfully_saves_all_data_to_db_when_no_error(
    data_db: Session, client: TestClient, superuser_header_token
):
    input_json = create_input_json_with_two_of_each_entity()

    response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": input_json},
        headers=superuser_header_token,
    )

    expected_collection_import_ids = ["test.new.collection.0", "test.new.collection.1"]
    expected_family_import_ids = ["test.new.family.0", "test.new.family.1"]
    expected_document_import_ids = ["test.new.document.0", "test.new.document.1"]
    expected_event_import_ids = ["test.new.event.0", "test.new.event.1"]

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        "message": "Bulk import request accepted. Check Cloudwatch logs for result."
    }

    saved_collections = (
        data_db.query(Collection)
        .filter(Collection.import_id.in_(expected_collection_import_ids))
        .all()
    )

    assert len(saved_collections) == 2
    for coll in saved_collections:
        assert coll.import_id in expected_collection_import_ids

    saved_families = (
        data_db.query(Family)
        .filter(Family.import_id.in_(expected_family_import_ids))
        .all()
    )

    assert len(saved_families) == 2
    for fam in saved_families:
        assert fam.import_id in expected_family_import_ids

    saved_documents = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id.in_(expected_document_import_ids))
        .all()
    )

    assert len(saved_documents) == 2
    for doc in saved_documents:
        assert doc.import_id in expected_document_import_ids
        assert doc.family_import_id in expected_family_import_ids

    saved_events = (
        data_db.query(FamilyEvent)
        .filter(FamilyEvent.import_id.in_(expected_event_import_ids))
        .all()
    )

    assert len(saved_events) == 2
    for ev in saved_events:
        assert ev.import_id in expected_event_import_ids
        assert ev.family_import_id in expected_family_import_ids


@pytest.mark.s3
def test_bulk_import_successfully_updates_already_imported_data_when_no_error(
    data_db: Session, client: TestClient, superuser_header_token
):
    original_data = {
        "collections": [default_collection],
        "families": [default_family],
        "documents": [default_document],
        "events": [default_event],
    }
    original_input_json = build_json_file(original_data)

    response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": original_input_json},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED

    updated_title = "Updated"
    updated_input_json = build_json_file(
        {
            "collections": [
                {**original_data["collections"][0], "title": updated_title}
            ],
            "families": [{**original_data["families"][0], "title": updated_title}],
            "documents": [{**original_data["documents"][0], "title": updated_title}],
            "events": [{**original_data["events"][0], "event_title": updated_title}],
        }
    )

    update_response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": updated_input_json},
        headers=superuser_header_token,
    )

    assert update_response.status_code == status.HTTP_202_ACCEPTED

    saved_collection = (
        data_db.query(Collection)
        .filter(Collection.import_id == original_data["collections"][0]["import_id"])
        .scalar()
    )
    saved_family = (
        data_db.query(Family)
        .filter(Family.import_id == original_data["families"][0]["import_id"])
        .scalar()
    )
    saved_document = (
        data_db.query(PhysicalDocument)
        .join(
            FamilyDocument, FamilyDocument.physical_document_id == PhysicalDocument.id
        )
        .filter(FamilyDocument.import_id == original_data["documents"][0]["import_id"])
        .scalar()
    )
    saved_event = (
        data_db.query(FamilyEvent)
        .filter(FamilyEvent.import_id == original_data["events"][0]["import_id"])
        .scalar()
    )
    updated_entities = {
        "collection": saved_collection.title,
        "family": saved_family.title,
        "document": saved_document.title,
        "event": saved_event.title,
    }

    for entity, title in updated_entities.items():
        assert updated_title == title, f"Updated title does not match for {entity}"


@pytest.mark.s3
def test_bulk_import_successfully_updates_document_when_user_language_has_changed(
    data_db: Session, client: TestClient, superuser_header_token
):
    original_data = {
        "collections": [default_collection],
        "families": [default_family],
        "documents": [default_document],
        "events": [default_event],
    }
    original_input_json = build_json_file(original_data)

    response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": original_input_json},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED

    updated_user_language_name = "German"
    updated_input_json = build_json_file(
        {
            **original_data,
            "documents": [
                {
                    **original_data["documents"][0],
                    "user_language_name": updated_user_language_name,
                }
            ],
        }
    )

    update_response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": updated_input_json},
        headers=superuser_header_token,
    )

    assert update_response.status_code == status.HTTP_202_ACCEPTED

    saved_document_language = (
        data_db.query(Language)
        .join(
            PhysicalDocumentLanguage,
            PhysicalDocumentLanguage.language_id == Language.id,
        )
        .join(
            PhysicalDocument,
            PhysicalDocument.id == PhysicalDocumentLanguage.document_id,
        )
        .join(
            FamilyDocument, FamilyDocument.physical_document_id == PhysicalDocument.id
        )
        .filter(FamilyDocument.import_id == original_data["documents"][0]["import_id"])
        .scalar()
    )

    assert updated_user_language_name == saved_document_language.name


@pytest.mark.s3
def test_bulk_import_successfully_updates_family_metadata_when_no_error(
    data_db: Session, client: TestClient, superuser_header_token
):
    original_data = {"families": [{**default_family, "collections": []}]}
    original_input_json = build_json_file(original_data)

    response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": original_input_json},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED

    updated_metadata = {
        **original_data["families"][0]["metadata"],
        "author_type": ["Party"],
    }
    updated_input_json = build_json_file(
        {
            "families": [
                {**original_data["families"][0], "metadata": updated_metadata},
            ]
        }
    )

    update_response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": updated_input_json},
        headers=superuser_header_token,
    )

    assert update_response.status_code == status.HTTP_202_ACCEPTED

    saved_family_metadata = (
        data_db.query(FamilyMetadata)
        .filter(
            FamilyMetadata.family_import_id == original_data["families"][0]["import_id"]
        )
        .scalar()
    )

    assert updated_metadata == saved_family_metadata.value


@pytest.mark.s3
def test_bulk_import_successfully_updates_family_collections_when_no_error(
    data_db: Session, client: TestClient, superuser_header_token
):
    original_data = {
        "collections": [default_collection],
        "families": [default_family],
    }
    original_input_json = build_json_file(original_data)

    response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": original_input_json},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED

    new_collection = {**default_collection, "import_id": "test.new.collection.1"}
    updated_data = {
        "collections": [new_collection],
        "families": [{**default_family, "collections": [new_collection["import_id"]]}],
    }
    updated_input_json = build_json_file(updated_data)

    update_response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": updated_input_json},
        headers=superuser_header_token,
    )

    assert update_response.status_code == status.HTTP_202_ACCEPTED

    saved_family_collections = (
        data_db.query(CollectionFamily)
        .filter(
            CollectionFamily.family_import_id
            == original_data["families"][0]["import_id"]
        )
        .all()
    )

    assert len(saved_family_collections) == 1
    assert (
        new_collection["import_id"] == saved_family_collections[0].collection_import_id
    )


@pytest.mark.s3
def test_bulk_import_successfully_updates_collection_metadata_when_no_error(
    data_db: Session, client: TestClient, superuser_header_token
):
    test_corpus_type = CorpusTypeCreateDTO(
        name="test",
        description="",
        metadata={
            "_collection": {
                "id": {"allow_any": True, "allow_blanks": True, "allowed_values": []}
            },
        },
    )
    corpus_type_repo.create(data_db, test_corpus_type)
    test_corpus = CorpusCreateDTO(
        import_id="test.corpus.0.1",
        title="",
        description="",
        organisation_id=1,
        corpus_text="",
        corpus_image_url="",
        corpus_type_name=test_corpus_type.name,
    )
    corpus_repo.create(data_db, test_corpus)

    original_data = {
        "collections": [{**default_collection, "metadata": {"id": ["111111"]}}]
    }
    original_input_json = build_json_file(original_data)

    response = client.post(
        f"/api/v1/bulk-import/{test_corpus.import_id}",
        files={"data": original_input_json},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED

    updated_metadata = {
        **original_data["collections"][0]["metadata"],
        "id": ["222222"],
    }
    updated_input_json = build_json_file(
        {
            "collections": [
                {**original_data["collections"][0], "metadata": updated_metadata},
            ]
        }
    )

    update_response = client.post(
        f"/api/v1/bulk-import/{test_corpus.import_id}",
        files={"data": updated_input_json},
        headers=superuser_header_token,
    )

    assert update_response.status_code == status.HTTP_202_ACCEPTED

    saved_family_metadata = data_db.query(Collection).scalar()

    assert updated_metadata == saved_family_metadata.valid_metadata


@pytest.mark.s3
def test_bulk_import_does_not_save_data_to_db_on_error(
    caplog,
    data_db: Session,
    client: TestClient,
    superuser_header_token,
    rollback_collection_repo,
):
    input_json = create_input_json_with_two_of_each_entity()

    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
            files={"data": input_json},
            headers=superuser_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert "Rolling back transaction due to the following error:" in caplog.text
    actual_collection = (
        data_db.query(Collection)
        .filter(Collection.import_id == "test.new.collection.0")
        .one_or_none()
    )
    assert actual_collection is None


@pytest.mark.s3
def test_bulk_import_only_saves_default_number_of_documents_if_no_limit_provided_in_request(
    data_db: Session, client: TestClient, superuser_header_token
):
    input_json = build_json_file(
        {
            "collections": [default_collection],
            "families": [default_family],
            "documents": [
                {**default_document, "import_id": f"test.new.document.{i}"}
                for i in range(DEFAULT_DOCUMENT_LIMIT + 1)
            ],
            "events": [default_event],
        }
    )

    response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": input_json},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        "message": "Bulk import request accepted. Check Cloudwatch logs for result."
    }

    assert (
        "Created"
        == data_db.query(FamilyDocument)
        .filter(
            FamilyDocument.import_id
            == f"test.new.document.{DEFAULT_DOCUMENT_LIMIT - 1}"
        )
        .one_or_none()
        .document_status
    )

    assert (
        not data_db.query(FamilyDocument)
        .filter(
            FamilyDocument.import_id == f"test.new.document.{DEFAULT_DOCUMENT_LIMIT}"
        )
        .one_or_none()
    )


def test_bulk_import_only_updates_number_of_documents_within_provided_limit(
    data_db: Session, client: TestClient, superuser_header_token
):
    original_data = {
        "families": [{**default_family, "collections": []}],
        "documents": [
            default_document,
            {**default_document, "import_id": "test.new.document.1"},
        ],
    }
    original_input_json = build_json_file(original_data)

    response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": original_input_json},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED

    updated_title = "Updated"
    updated_input_json = build_json_file(
        {
            **original_data,
            "documents": [
                {**original_data["documents"][0], "title": updated_title},
                {**original_data["documents"][1], "title": updated_title},
            ],
        }
    )

    update_response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        files={"data": updated_input_json},
        headers=superuser_header_token,
        params={"document_limit": 1},
    )

    assert update_response.status_code == status.HTTP_202_ACCEPTED

    saved_document_1_title = (
        data_db.query(PhysicalDocument)
        .join(
            FamilyDocument, FamilyDocument.physical_document_id == PhysicalDocument.id
        )
        .filter(FamilyDocument.import_id == original_data["documents"][0]["import_id"])
        .one_or_none()
        .title
    )

    saved_document_2_title = (
        data_db.query(PhysicalDocument)
        .join(
            FamilyDocument, FamilyDocument.physical_document_id == PhysicalDocument.id
        )
        .filter(FamilyDocument.import_id == original_data["documents"][1]["import_id"])
        .one_or_none()
        .title
    )

    assert updated_title == saved_document_1_title
    assert original_data["documents"][1]["title"] == saved_document_2_title


@pytest.mark.s3
def test_bulk_import_idempotency_on_create(
    caplog,
    data_db: Session,
    client: TestClient,
    superuser_header_token,
):
    input_json = build_json_file(
        {
            "collections": [default_collection],
            "families": [default_family],
            "documents": [
                default_document,
                {**default_document, "import_id": "test.new.document.1"},
            ],
            "events": [default_event],
        }
    )

    with caplog.at_level(logging.ERROR):
        first_response = client.post(
            "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
            files={"data": input_json},
            params={"document_limit": 1},
            headers=superuser_header_token,
        )

        assert first_response.status_code == status.HTTP_202_ACCEPTED
        assert first_response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert (
        "Created"
        == data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.0")
        .one_or_none()
        .document_status
    )

    assert (
        not data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.1")
        .one_or_none()
    )

    # simulating pipeline ingest
    data_db.execute(
        update(FamilyDocument)
        .where(FamilyDocument.import_id == "test.new.document.0")
        .values(document_status="Published")
    )

    with caplog.at_level(logging.ERROR):
        second_response = client.post(
            "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
            files={"data": input_json},
            params={"document_limit": 1},
            headers=superuser_header_token,
        )

        assert second_response.status_code == status.HTTP_202_ACCEPTED
        assert second_response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    # checking that subsequent bulk import does not change the status
    assert (
        "Published"
        == data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.0")
        .one_or_none()
        .document_status
    )

    assert (
        "Created"
        == data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "test.new.document.1")
        .one_or_none()
        .document_status
    )


@pytest.mark.s3
def test_generates_unique_slugs_for_documents_with_identical_titles_on_create(
    caplog,
    data_db: Session,
    client: TestClient,
    superuser_header_token,
):
    """
    This test ensures that given multiple documents with the same title a unique slug
    is generated for each and thus the documents can be saved to the DB at the end
    of bulk import. However, the current length of the suffix added to the slug
    to ensure uniqueness (6), means that the likelihood of a collision is extremely low,
    which makes it extremely difficult to write a consistently failing test.
    So in most cases, this test will pass simply because there no slugs were duplicated.
    """

    input_json = build_json_file(
        {
            "families": [{**default_family, "collections": []}],
            "documents": [
                {**default_document, "import_id": f"test.new.document.{i}"}
                for i in range(1000)
            ],
        }
    )

    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
            files={"data": input_json},
            headers=superuser_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    saved_documents = data_db.query(FamilyDocument).all()
    saved_unique_slugs = set(doc.slugs[0].name for doc in saved_documents)
    # check all created slugs are unique
    assert len(saved_documents) == len(saved_unique_slugs)


@pytest.mark.s3
def test_generates_unique_slugs_for_documents_with_identical_titles_on_update(
    caplog,
    data_db: Session,
    client: TestClient,
    superuser_header_token,
):
    """
    This test ensures that given multiple documents with the same title a unique slug
    is generated for each and thus the documents can be saved to the DB at the end
    of bulk import. However, the current length of the suffix added to the slug
    to ensure uniqueness (6), means that the likelihood of a collision is extremely low,
    which makes it extremely difficult to write a consistently failing test.
    So in most cases, this test will pass simply because there no slugs were duplicated.
    """
    input_data = {
        "families": [{**default_family, "collections": []}],
        "documents": [
            {**default_document, "import_id": f"test.new.document.{i}"}
            for i in range(1000)
        ],
    }

    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
            files={"data": build_json_file(input_data)},
            headers=superuser_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED

    updated_data = {
        **input_data,
        "documents": [{**doc, "title": "Updated"} for doc in input_data["documents"]],
    }

    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
            files={"data": build_json_file(updated_data)},
            headers=superuser_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED

    saved_documents = data_db.query(FamilyDocument).all()
    saved_unique_slugs = set(doc.slugs[0].name for doc in saved_documents)

    assert all(slug.startswith("updated") for slug in saved_unique_slugs)
    # check all updated slugs are unique
    assert len(saved_documents) == len(saved_unique_slugs)


@pytest.mark.s3
def test_bulk_import_returns_bad_request_response_when_corpus_import_id_invalid(
    client: TestClient,
    data_db: Session,
    superuser_header_token,
):
    invalid_corpus = "test"
    input_json = create_input_json_with_two_of_each_entity()

    response = client.post(
        f"/api/v1/bulk-import/{invalid_corpus}",
        files={"data": input_json},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": f"No corpus found for import_id: {invalid_corpus}"
    }


@pytest.mark.s3
def test_bulk_import_events_when_event_type_invalid(
    caplog,
    data_db: Session,
    client: TestClient,
    superuser_header_token,
):

    input_json = build_json_file(
        {
            "families": [{**default_family, "collections": []}],
            "documents": [default_document],
            "events": [{**default_event, "event_type_value": "Invalid"}],
        }
    )

    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
            files={"data": input_json},
            headers=superuser_header_token,
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }

    assert (
        "Metadata validation failed: Invalid value '['Invalid']' for metadata key 'event_type'"
        in caplog.text
    )


def test_bulk_import_when_not_authorised(client: TestClient, data_db: Session):
    response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_bulk_import_admin_non_super(
    client: TestClient, data_db: Session, admin_user_header_token
):
    response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        headers=admin_user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"] == "User admin@cpr.org is not authorised to CREATE a BULK_IMPORT"
    )


def test_bulk_import_non_super_non_admin(
    client: TestClient, data_db: Session, user_header_token
):
    response = client.post(
        "/api/v1/bulk-import/UNFCCC.corpus.i00000001.n0000",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"] == "User cclw@cpr.org is not authorised to CREATE a BULK_IMPORT"
    )
