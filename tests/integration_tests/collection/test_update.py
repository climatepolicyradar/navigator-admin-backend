from db_client.models.dfce.collection import (
    Collection,
    CollectionFamily,
    CollectionOrganisation,
)
from db_client.models.dfce.family import Slug
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.model.collection import CollectionWriteDTO
from tests.helpers.collection import create_collection_write_dto
from tests.integration_tests.setup_db import EXPECTED_COLLECTIONS, setup_db


def test_update_collection_no_metadata(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_collection = CollectionWriteDTO(
        title="Updated Title", description="just a test", organisation="CCLW"
    )
    response = client.put(
        "/api/v1/collections/C.0.0.2",
        json=new_collection.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "just a test"
    assert data["metadata"] == {}

    db_collection: Collection = (
        data_db.query(Collection).filter(Collection.import_id == "C.0.0.2").one()
    )
    assert db_collection.title == "Updated Title"
    assert db_collection.description == "just a test"
    assert db_collection.valid_metadata == {}

    families = data_db.query(CollectionFamily).filter(
        CollectionFamily.collection_import_id == "C.0.0.2"
    )
    assert families.count() == 2
    org: CollectionOrganisation = (
        data_db.query(CollectionOrganisation)
        .filter(CollectionOrganisation.collection_import_id == "C.0.0.2")
        .one()
    )
    assert org is not None


def test_update_collection_with_metadata(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_collection = create_collection_write_dto(
        title="Updated Title", description="just a test", metadata={"key": "value"}
    )
    response = client.put(
        "/api/v1/collections/C.0.0.2",
        json=new_collection.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "just a test"
    assert data["metadata"] == {"key": "value"}

    db_collection: Collection = (
        data_db.query(Collection).filter(Collection.import_id == "C.0.0.2").one()
    )
    assert db_collection.title == "Updated Title"
    assert db_collection.description == "just a test"
    assert db_collection.valid_metadata == {"key": "value"}

    families = data_db.query(CollectionFamily).filter(
        CollectionFamily.collection_import_id == "C.0.0.2"
    )
    assert families.count() == 2
    org: CollectionOrganisation = (
        data_db.query(CollectionOrganisation)
        .filter(CollectionOrganisation.collection_import_id == "C.0.0.2")
        .one()
    )
    assert org is not None


def test_update_collections_updates_associated_slug(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_collection = create_collection_write_dto(
        title="This is the updated title of this collection",
        description="just a test",
    )
    response = client.put(
        "/api/v1/collections/C.0.0.2",
        json=new_collection.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "This is the updated title of this collection"
    assert data["description"] == "just a test"

    slug = (
        data_db.query(Slug).filter(Slug.collection_import_id == "C.0.0.2").one_or_none()
    )
    assert slug is not None

    assert "this-is-the-updated-title-of-this-collection" in slug.name


def test_update_collection_when_not_authorised(client: TestClient, data_db: Session):
    setup_db(data_db)
    new_collection = create_collection_write_dto(
        title="Updated Title",
        description="just a test",
    )
    response = client.put(
        "/api/v1/collections/C.0.0.2", json=new_collection.model_dump()
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_collection_idempotent(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    collection = EXPECTED_COLLECTIONS[1]
    response = client.put(
        f"/api/v1/collections/{collection['import_id']}",
        json=collection,
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == EXPECTED_COLLECTIONS[1]["title"]
    assert data["description"] == EXPECTED_COLLECTIONS[1]["description"]
    db_collection: Collection = (
        data_db.query(Collection)
        .filter(Collection.import_id == EXPECTED_COLLECTIONS[1]["import_id"])
        .one()
    )
    assert db_collection.title == EXPECTED_COLLECTIONS[1]["title"]
    assert db_collection.description == EXPECTED_COLLECTIONS[1]["description"]


def test_update_collection_rollback(
    client: TestClient, data_db: Session, rollback_collection_repo, user_header_token
):
    setup_db(data_db)
    new_collection = create_collection_write_dto(
        title="Updated Title",
        description="just a test",
    )
    response = client.put(
        "/api/v1/collections/C.0.0.2",
        json=new_collection.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    db_collection: Collection = (
        data_db.query(Collection).filter(Collection.import_id == "C.0.0.2").one()
    )
    assert db_collection.title != "Updated Title"
    assert db_collection.description != "just a test"

    families = data_db.query(CollectionFamily).filter(
        CollectionFamily.collection_import_id == "C.0.0.2"
    )
    assert families.count() == 2
    org: CollectionOrganisation = (
        data_db.query(CollectionOrganisation)
        .filter(CollectionOrganisation.collection_import_id == "C.0.0.2")
        .one()
    )
    assert org is not None
    assert rollback_collection_repo.update.call_count == 1


def test_update_collection_when_not_found(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_collection = create_collection_write_dto(
        title="Updated Title",
        description="just a test",
    )
    response = client.put(
        "/api/v1/collections/C.0.0.22",
        json=new_collection.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Collection not updated: C.0.0.22"


def test_update_collection_when_db_error(
    client: TestClient, data_db: Session, bad_collection_repo, user_header_token
):
    setup_db(data_db)
    new_collection = create_collection_write_dto(
        title="Updated Title",
        description="just a test",
    )
    response = client.put(
        "/api/v1/collections/C.0.0.2",
        json=new_collection.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_collection_repo.update.call_count == 1
