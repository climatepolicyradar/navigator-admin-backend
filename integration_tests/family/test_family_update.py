from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from app.clients.db.models.law_policy.family import Family, FamilyCategory, Slug
from app.clients.db.models.law_policy.metadata import FamilyMetadata
from integration_tests.setup_db import EXPECTED_FAMILIES, setup_db
from unit_tests.helpers.family import create_family_dto


def test_update_family(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.2",
        title="Updated Title",
        summary="just a test",
        geography="USA",
        category=FamilyCategory.UNFCCC,
        metadata={"color": "pink", "size": 0},
        slug="new-slug",
    )
    response = client.put(
        "/api/v1/families", json=new_family.dict(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["summary"] == "just a test"
    assert data["geography"] == "USA"
    assert data["category"] == "UNFCCC"
    assert data["slug"].startswith("updated-title")

    db_family: Family = (
        test_db.query(Family).filter(Family.import_id == "A.0.0.2").one()
    )
    assert db_family.title == "Updated Title"
    assert db_family.description == "just a test"
    assert db_family.geography_id == 210
    assert db_family.family_category == "UNFCCC"
    db_slug = test_db.query(Slug).filter(Slug.family_import_id == "A.0.0.2").all()
    assert len(db_slug) == 1
    assert str(db_slug[0].name).startswith("updated-title")


def test_update_family_when_not_authenticated(client: TestClient, test_db: Session):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.2",
        title="Updated Title",
        summary="just a test",
        geography="USA",
        category=FamilyCategory.UNFCCC,
        metadata={"color": "pink", "size": 0},
        slug="new-slug",
    )
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_family_idempotent_when_ok(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    family = EXPECTED_FAMILIES[1]
    response = client.put("/api/v1/families", json=family, headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == EXPECTED_FAMILIES[1]["title"]
    assert data["summary"] == EXPECTED_FAMILIES[1]["summary"]
    assert data["geography"] == EXPECTED_FAMILIES[1]["geography"]
    assert data["category"] == EXPECTED_FAMILIES[1]["category"]
    db_family: Family = (
        test_db.query(Family)
        .filter(Family.import_id == EXPECTED_FAMILIES[1]["import_id"])
        .one()
    )
    assert db_family.title == EXPECTED_FAMILIES[1]["title"]
    assert db_family.description == EXPECTED_FAMILIES[1]["summary"]
    assert db_family.geography_id == 1
    assert db_family.family_category == EXPECTED_FAMILIES[1]["category"]


def test_update_family_rollback(
    client: TestClient, test_db: Session, rollback_family_repo, user_header_token
):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.2",
        title="Updated Title",
        summary="just a test",
        metadata={"color": "pink", "size": 0},
    )
    response = client.put(
        "/api/v1/families", json=new_family.dict(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    db_family: Family = (
        test_db.query(Family).filter(Family.import_id == "A.0.0.2").one()
    )
    assert db_family.title != "Updated Title"
    assert db_family.description != "just a test"

    db_slug = test_db.query(Slug).filter(Slug.family_import_id == "A.0.0.2").all()
    # Ensure no slug was created
    assert len(db_slug) == 0

    db_meta = (
        test_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == "A.0.0.2")
        .all()
    )
    # Ensure no metadata was updated
    assert len(db_meta) == 1
    assert db_meta[0].value == {"size": 4, "color": "green"}


def test_update_family_when_not_found(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.22",
        title="Updated Title",
        summary="just a test",
        metadata={"color": "pink", "size": 0},
    )
    response = client.put(
        "/api/v1/families", json=new_family.dict(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not updated: A.0.0.22"


def test_update_family_when_db_error(
    client: TestClient, test_db: Session, bad_family_repo, user_header_token
):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.22",
        title="Updated Title",
        summary="just a test",
        metadata={"color": "pink", "size": 0},
    )
    response = client.put(
        "/api/v1/families", json=new_family.dict(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_update_family__invalid_geo(
    client: TestClient, test_db: Session, bad_family_repo, user_header_token
):
    setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.22",
        title="Updated Title",
        summary="just a test",
        metadata={"color": "pink", "size": 0},
    )
    new_family.geography = "UK"
    response = client.put(
        "/api/v1/families", json=new_family.dict(), headers=user_header_token
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "The geography value UK is invalid!"


def test_update_family_metadata_if_changed(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    expected_meta = {"color": "pink", "size": 23}
    response = client.get(
        "/api/v1/families/A.0.0.2",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    family_data = response.json()
    assert {"color": "green", "size": 4} == family_data["metadata"]
    family_data["metadata"] = expected_meta
    response = client.put(
        "/api/v1/families", json=family_data, headers=user_header_token
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert expected_meta == data["metadata"]

    metadata: FamilyMetadata = (
        test_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == "A.0.0.2")
        .one()
    )
    assert metadata.value == expected_meta
