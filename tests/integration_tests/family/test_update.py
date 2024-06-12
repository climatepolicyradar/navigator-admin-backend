from typing import Optional

from db_client.models.dfce.collection import CollectionFamily
from db_client.models.dfce.family import Family, FamilyCategory, Geography, Slug
from db_client.models.dfce.metadata import FamilyMetadata
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.family import create_family_write_dto
from tests.integration_tests.setup_db import DEFAULT_GEO_ID, EXPECTED_FAMILIES, setup_db

USA_GEO_ID = 212


def test_update_family(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="apple",
        summary="just a test",
        geography="USA",
        category=FamilyCategory.UNFCCC,
        metadata={"color": ["pink"], "size": [0]},
        collections=["C.0.0.3"],
    )
    response = client.put(
        "/api/v1/families/A.0.0.1",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "apple"
    assert data["summary"] == "just a test"
    assert data["geography"] == "USA"
    assert data["category"] == "UNFCCC"
    assert data["collections"] == ["C.0.0.3"]

    db_family: Family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.1").one()
    )
    assert db_family.title == "apple"
    assert db_family.description == "just a test"
    assert db_family.geography_id == USA_GEO_ID
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[-1].name) == data["slug"]

    db_collection: Optional[list[CollectionFamily]] = (
        data_db.query(CollectionFamily)
        .filter(CollectionFamily.collection_import_id == "C.0.0.3")
        .all()
    )
    assert len(db_collection) == 1
    assert db_collection[0].family_import_id == "A.0.0.1"


def test_update_family_slug(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="Updated Title",
        summary="",
        geography="South Asia",
        category=FamilyCategory.UNFCCC,
        metadata={"color": ["red"], "size": [3]},
        collections=["C.0.0.2"],
    )

    response = client.put(
        "/api/v1/families/A.0.0.1",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["summary"] == ""
    assert data["geography"] == "South Asia"
    assert data["category"] == "UNFCCC"
    assert data["slug"].startswith("updated-title")
    assert data["collections"] == ["C.0.0.2"]

    db_family: Family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.1").one()
    )
    assert db_family.title == "Updated Title"
    assert db_family.description == ""
    expected_geo = (
        data_db.query(Geography).filter(Geography.display_value == "South Asia").one()
    )

    assert db_family.geography_id == expected_geo.id
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 2
    assert str(db_slug[-1].name).startswith("updated-title")

    db_collection: Optional[list[CollectionFamily]] = (
        data_db.query(CollectionFamily)
        .filter(CollectionFamily.family_import_id == "A.0.0.1")
        .all()
    )
    assert len(db_collection) == 1
    assert db_collection[0].collection_import_id == "C.0.0.2"


def test_update_family_remove_collections(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="apple",
        summary="",
        geography="Other",
        category=FamilyCategory.UNFCCC,
        metadata={"color": ["red"], "size": [3]},
        collections=[],
    )
    response = client.put(
        "/api/v1/families/A.0.0.1",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "apple"
    assert data["summary"] == ""
    assert data["geography"] == "Other"
    assert data["category"] == "UNFCCC"
    assert data["slug"] == "Slug1"
    assert data["collections"] == []

    db_family: Family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.1").one()
    )
    assert db_family.title == "apple"
    assert db_family.description == ""
    expected_geo = (
        data_db.query(Geography).filter(Geography.display_value == "Other").one()
    )
    assert db_family.geography_id == expected_geo.id
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[-1].name) == "Slug1"

    db_collection: CollectionFamily = (
        data_db.query(CollectionFamily)
        .filter(CollectionFamily.family_import_id == "A.0.0.1")
        .one_or_none()
    )
    assert db_collection is None


def test_update_family_append_collections(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="apple",
        summary="",
        geography="Other",
        category=FamilyCategory.UNFCCC,
        metadata={"color": ["red"], "size": [3]},
        collections=["C.0.0.2", "C.0.0.3"],
    )
    response = client.put(
        "/api/v1/families/A.0.0.1",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "apple"
    assert data["summary"] == ""
    assert data["geography"] == "Other"
    assert data["category"] == "UNFCCC"
    assert data["slug"] == "Slug1"
    assert data["collections"] == ["C.0.0.2", "C.0.0.3"]

    db_family: Family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.1").one()
    )
    assert db_family.title == "apple"
    assert db_family.description == ""

    expected_geo = (
        data_db.query(Geography).filter(Geography.display_value == "Other").one()
    )
    assert db_family.geography_id == expected_geo.id
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[-1].name) == "Slug1"

    db_collections: Optional[list[CollectionFamily]] = (
        data_db.query(CollectionFamily)
        .filter(CollectionFamily.family_import_id == "A.0.0.1")
        .all()
    )
    assert len(db_collections) == 2
    assert db_collections[0].collection_import_id == "C.0.0.2"
    assert db_collections[1].collection_import_id == "C.0.0.3"


def test_update_family_collections_to_one_that_does_not_exist(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="apple",
        summary="",
        geography="Other",
        category=FamilyCategory.UNFCCC,
        metadata={"color": ["red"], "size": [3]},
        collections=["C.0.0.2", "X.Y.Z.3"],
    )
    response = client.put(
        "/api/v1/families/A.0.0.1",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "One or more of the collections to update does not exist"

    db_family: Family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.1").one()
    )
    assert db_family.title == "apple"
    assert db_family.description == ""

    expected_geo = (
        data_db.query(Geography).filter(Geography.display_value == "Other").one()
    )
    assert db_family.geography_id == expected_geo.id
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[-1].name) == "Slug1"

    db_collections: Optional[list[CollectionFamily]] = (
        data_db.query(CollectionFamily)
        .filter(CollectionFamily.family_import_id == "A.0.0.1")
        .all()
    )
    assert len(db_collections) == 1
    assert db_collections[0].collection_import_id == "C.0.0.2"


def test_update_fails_family_when_user_org_different_to_family_org(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="Updated Title",
        summary="just a test",
        geography="USA",
        category=FamilyCategory.UNFCCC,
        metadata={"color": ["pink"], "size": [0]},
        collections=[],
    )
    response = client.put(
        "/api/v1/families/A.0.0.2",
        json=new_family.model_dump(),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"]
        == "User 'unfccc@cpr.org' is not authorised to perform operation on 'CCLW.corpus.i00000001.n0000'"
    )

    db_family: Family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.2").one()
    )
    assert db_family.title == "apple orange banana"
    assert db_family.description == "apple"
    assert db_family.geography_id == DEFAULT_GEO_ID
    assert db_family.family_category == "UNFCCC"


def test_update_family_succeeds_when_user_org_different_to_family_org_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="apple",
        summary="just a test",
        geography="USA",
        category=FamilyCategory.UNFCCC,
        metadata={"color": ["pink"], "size": [0]},
        collections=["C.0.0.3"],
    )
    response = client.put(
        "/api/v1/families/A.0.0.1",
        json=new_family.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "apple"
    assert data["summary"] == "just a test"
    assert data["geography"] == "USA"
    assert data["category"] == "UNFCCC"
    assert data["collections"] == ["C.0.0.3"]

    db_family: Family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.1").one()
    )
    assert db_family.title == "apple"
    assert db_family.description == "just a test"
    assert db_family.geography_id == USA_GEO_ID
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[-1].name) == data["slug"]

    db_collection: Optional[list[CollectionFamily]] = (
        data_db.query(CollectionFamily)
        .filter(CollectionFamily.collection_import_id == "C.0.0.3")
        .all()
    )
    assert len(db_collection) == 1
    assert db_collection[0].family_import_id == "A.0.0.1"


def test_update_family_when_collection_org_different_to_family_org(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        metadata={"color": ["pink"], "size": [0]},
        collections=["C.0.0.1", "C.0.0.2", "C.0.0.3"],
    )
    response = client.put(
        "/api/v1/families/A.0.0.1",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert (
        data["detail"]
        == "Organisation mismatch between some collections and the current user"
    )

    db_families: Optional[list[Family]] = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.1").all()
    )
    assert len(db_families) == 1
    db_family = db_families[0]
    assert db_family.title == "apple"
    assert db_family.description == ""
    assert db_family.geography_id == DEFAULT_GEO_ID
    assert db_family.family_category == "UNFCCC"


def test_update_family_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="Updated Title",
        summary="just a test",
        geography="USA",
        category=FamilyCategory.UNFCCC,
        metadata={"color": ["pink"], "size": [0]},
    )
    response = client.put("/api/v1/families/A.0.0.2", json=new_family.model_dump())
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_family_idempotent_when_ok(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    family = EXPECTED_FAMILIES[1]
    response = client.put(
        f"/api/v1/families/{family['import_id']}",
        json=family,
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == EXPECTED_FAMILIES[1]["title"]
    assert data["summary"] == EXPECTED_FAMILIES[1]["summary"]
    assert data["geography"] == EXPECTED_FAMILIES[1]["geography"]
    assert data["category"] == EXPECTED_FAMILIES[1]["category"]
    db_family: Family = (
        data_db.query(Family)
        .filter(Family.import_id == EXPECTED_FAMILIES[1]["import_id"])
        .one()
    )
    assert db_family.title == EXPECTED_FAMILIES[1]["title"]
    assert db_family.description == EXPECTED_FAMILIES[1]["summary"]
    assert db_family.geography_id == DEFAULT_GEO_ID
    assert db_family.family_category == EXPECTED_FAMILIES[1]["category"]


# TODO: Fix with PDCT-1115
# def test_update_family_rollback(
#     client: TestClient, test_db: Session, rollback_family_repo, user_header_token
# ):
#     setup_db(test_db)
#     new_family = create_family_write_dto(
#         title="Updated Title",
#         summary="just a test",
#         metadata={"color": ["pink"], "size": [0]},
#     )
#     response = client.put(
#         "/api/v1/families/A.0.0.2",
#         json=new_family.model_dump(),
#         headers=user_header_token,
#     )
#     assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

#     db_family: Family = (
#         test_db.query(Family).filter(Family.import_id == "A.0.0.2").one()
#     )
#     assert db_family.title != "Updated Title"
#     assert db_family.description != "just a test"

#     db_slug = test_db.query(Slug).filter(Slug.family_import_id == "A.0.0.2").all()
#     # Ensure no extra slug was created
#     assert len(db_slug) == 1

#     db_meta = (
#         test_db.query(FamilyMetadata)
#         .filter(FamilyMetadata.family_import_id == "A.0.0.2")
#         .all()
#     )
#     # Ensure no metadata was updated
#     assert len(db_meta) == 1
#     assert db_meta[0].value == {"size": [4], "color": ["green"]}


def test_update_family_when_not_found(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="Updated Title",
        summary="just a test",
        metadata={"color": ["pink"], "size": [0]},
    )
    response = client.put(
        "/api/v1/families/A.0.0.22",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not updated: A.0.0.22"


def test_update_family_when_db_error(
    client: TestClient, data_db: Session, bad_family_repo, user_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="Updated Title",
        summary="just a test",
        metadata={"color": ["pink"], "size": [0]},
    )
    response = client.put(
        "/api/v1/families/A.0.0.22",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_update_family__invalid_geo(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="Updated Title",
        summary="just a test",
        metadata={"color": ["pink"], "size": [0]},
    )
    new_family.geography = "UK"
    response = client.put(
        "/api/v1/families/A.0.0.3",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "The geography value UK is invalid!"


def test_update_family_metadata_if_changed(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    expected_meta = {"color": ["pink"], "size": [23]}
    response = client.get(
        "/api/v1/families/A.0.0.2",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    family_data = response.json()
    assert {"color": ["green"], "size": [4]} == family_data["metadata"]
    family_data["metadata"] = expected_meta
    response = client.put(
        "/api/v1/families/A.0.0.2", json=family_data, headers=user_header_token
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert expected_meta == data["metadata"]

    metadata: FamilyMetadata = (
        data_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == "A.0.0.2")
        .one()
    )
    assert metadata.value == expected_meta
