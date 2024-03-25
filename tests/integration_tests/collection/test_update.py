from db_client.models.dfce.collection import (
    Collection,
    CollectionFamily,
    CollectionOrganisation,
)
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.collection import create_collection_write_dto
from tests.integration_tests.setup_db import EXPECTED_COLLECTIONS, setup_db


def test_update_collection(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    new_collection = create_collection_write_dto(
        title="Updated Title",
        description="just a test",
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

    db_collection: Collection = (
        test_db.query(Collection).filter(Collection.import_id == "C.0.0.2").one()
    )
    assert db_collection.title == "Updated Title"
    assert db_collection.description == "just a test"
    families = test_db.query(CollectionFamily).filter(
        CollectionFamily.collection_import_id == "C.0.0.2"
    )
    assert families.count() == 2
    org: CollectionOrganisation = (
        test_db.query(CollectionOrganisation)
        .filter(CollectionOrganisation.collection_import_id == "C.0.0.2")
        .one()
    )
    assert org is not None


def test_update_collection_when_not_authorised(client: TestClient, test_db: Session):
    setup_db(test_db)
    new_collection = create_collection_write_dto(
        title="Updated Title",
        description="just a test",
    )
    response = client.put(
        "/api/v1/collections/C.0.0.2", json=new_collection.model_dump()
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_collection_idempotent(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
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
        test_db.query(Collection)
        .filter(Collection.import_id == EXPECTED_COLLECTIONS[1]["import_id"])
        .one()
    )
    assert db_collection.title == EXPECTED_COLLECTIONS[1]["title"]
    assert db_collection.description == EXPECTED_COLLECTIONS[1]["description"]


def test_update_collection_rollback(
    client: TestClient, test_db: Session, rollback_collection_repo, user_header_token
):
    setup_db(test_db)
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
        test_db.query(Collection).filter(Collection.import_id == "C.0.0.2").one()
    )
    assert db_collection.title != "Updated Title"
    assert db_collection.description != "just a test"

    families = test_db.query(CollectionFamily).filter(
        CollectionFamily.collection_import_id == "C.0.0.2"
    )
    assert families.count() == 2
    org: CollectionOrganisation = (
        test_db.query(CollectionOrganisation)
        .filter(CollectionOrganisation.collection_import_id == "C.0.0.2")
        .one()
    )
    assert org is not None
    assert rollback_collection_repo.update.call_count == 1


def test_update_collection_when_not_found(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
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
    client: TestClient, test_db: Session, bad_collection_repo, user_header_token
):
    setup_db(test_db)
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
