from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from app.clients.db.models.law_policy.family import Family, Slug
from app.clients.db.models.law_policy.metadata import FamilyMetadata
from integration_tests.setup_db import setup_db
from unit_tests.helpers.family import create_family_dto


def test_create_family(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    test_meta = {"color": "blue", "size": 888}
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
        metadata=test_meta,
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Title"
    assert data["summary"] == "test test test"
    actual_family = test_db.query(Family).filter(Family.import_id == "A.0.0.9").one()
    assert actual_family.title == "Title"
    assert actual_family.description == "test test test"
    metadata = (
        test_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == "A.0.0.9")
        .one()
    )
    assert metadata.value is not None
    assert metadata.value == test_meta


def test_create_family_when_not_authorised(client: TestClient, test_db: Session):
    setup_db(test_db)
    test_meta = {"color": "blue", "size": 888}
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
        metadata=test_meta,
    )
    response = client.post(
        "/api/v1/families",
        json=new_family.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_family_rollback(
    client: TestClient, test_db: Session, rollback_family_repo, user_header_token
):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
        metadata={"color": "pink", "size": 0},
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    actual_family = (
        test_db.query(Family).filter(Family.import_id == "A.0.0.9").one_or_none()
    )
    assert actual_family is None
    db_slug = test_db.query(Slug).filter(Slug.family_import_id == "A.0.0.9").all()
    # Ensure no slug was created
    assert len(db_slug) == 0
    assert rollback_family_repo.create.call_count == 1


def test_create_family_when_db_error(
    client: TestClient, test_db: Session, bad_family_repo, user_header_token
):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
        metadata={"color": "pink", "size": 0},
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_family_repo.create.call_count == 1


def test_create_family_when_invalid_geo(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
    )
    new_family.geography = "UK"
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "The geography value UK is invalid!"


def test_create_family_when_invalid_category(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
    )
    new_family.category = "invalid"
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Invalid is not a valid FamilyCategory"


def test_create_family_when_invalid_org(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
    )
    new_family.organisation = "chicken"
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "The organisation name chicken is invalid!"
