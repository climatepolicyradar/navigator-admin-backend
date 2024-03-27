from db_client.models.dfce.collection import Collection
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.collection import create_collection_create_dto
from tests.integration_tests.setup_db import setup_db


def test_create_collection(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    new_collection = create_collection_create_dto(
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
    assert data == "CCLW.collection.i00000001.n0000"
    actual_collection = (
        data_db.query(Collection).filter(Collection.import_id == data).one()
    )
    assert actual_collection.title == "Title"
    assert actual_collection.description == "test test test"


def test_create_collection_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    new_collection = create_collection_create_dto(
        title="Title",
        description="test test test",
    )
    response = client.post(
        "/api/v1/collections",
        json=new_collection.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_collection_rollback(
    client: TestClient, data_db: Session, rollback_collection_repo, user_header_token
):
    setup_db(data_db)
    new_collection = create_collection_create_dto(
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
        data_db.query(Collection)
        .filter(Collection.import_id == "A.0.0.9")
        .one_or_none()
    )
    assert actual_collection is None
    assert rollback_collection_repo.create.call_count == 1


def test_create_collection_when_db_error(
    client: TestClient, data_db: Session, bad_collection_repo, user_header_token
):
    setup_db(data_db)
    new_collection = create_collection_create_dto(
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
