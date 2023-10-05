from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from app.clients.db.models.law_policy.collection import Collection
from integration_tests.setup_db import setup_db
from unit_tests.helpers.collection import create_write_collection_dto


def test_create_collection(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    new_collection = create_write_collection_dto(
        title="Title",
        description="test test test",
    )
    response = client.post(
        "/api/v1/collections",
        json=new_collection.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Title"
    assert data["description"] == "test test test"

    actual_collection = (
        test_db.query(Collection).filter(Collection.import_id == "C.0.0.9").one()
    )
    assert actual_collection.title == "Title"
    assert actual_collection.description == "test test test"


def test_create_collection_when_not_authenticated(client: TestClient, test_db: Session):
    setup_db(test_db)
    new_collection = create_write_collection_dto(
        title="Title",
        description="test test test",
    )
    response = client.post(
        "/api/v1/collections",
        json=new_collection.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_collection_rollback(
    client: TestClient, test_db: Session, rollback_collection_repo, user_header_token
):
    setup_db(test_db)
    new_collection = create_write_collection_dto(
        title="Title",
        description="test test test",
    )
    response = client.post(
        "/api/v1/collections",
        json=new_collection.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    actual_collection = (
        test_db.query(Collection)
        .filter(Collection.import_id == "A.0.0.9")
        .one_or_none()
    )
    assert actual_collection is None
    assert rollback_collection_repo.create.call_count == 1


def test_create_collection_when_db_error(
    client: TestClient, test_db: Session, bad_collection_repo, user_header_token
):
    setup_db(test_db)
    new_collection = create_write_collection_dto(
        title="Title",
        description="test test test",
    )
    response = client.post(
        "/api/v1/collections",
        json=new_collection.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_collection_repo.create.call_count == 1


def test_create_collection_when_org_invalid(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_collection = create_write_collection_dto(
        title="Title",
        description="test test test",
    )
    new_collection.organisation = "chicken"
    response = client.post(
        "/api/v1/collections",
        json=new_collection.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "The organisation name chicken is invalid!"
