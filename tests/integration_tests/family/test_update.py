from typing import Optional

from db_client.models.dfce.collection import CollectionFamily
from db_client.models.dfce.family import Family, FamilyCategory, Geography, Slug
from db_client.models.dfce.metadata import FamilyMetadata
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.family import create_family_write_dto
from tests.integration_tests.setup_db import EXPECTED_FAMILIES, add_data, setup_db

USA_GEO_ID = 209


def test_update_family(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="apple",
        summary="just a test",
        geographies=["USA"],
        category=FamilyCategory.UNFCCC,
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
    assert USA_GEO_ID in [g.id for g in db_family.geographies]
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[0].name) == data["slug"]

    db_collection: Optional[list[CollectionFamily]] = (
        data_db.query(CollectionFamily)
        .filter(CollectionFamily.collection_import_id == "C.0.0.3")
        .all()
    )
    assert len(db_collection) == 1
    assert db_collection[0].family_import_id == "A.0.0.1"


def test_update_family_geographies(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)

    family_1 = create_family_write_dto(
        title="apple",
        summary="just a test",
        geographies=["USA", "GBR"],
        category=FamilyCategory.UNFCCC,
        collections=[],
    )
    family_2 = create_family_write_dto(
        title="apple",
        summary="just a test",
        geographies=["USA", "AUS"],
        category=FamilyCategory.UNFCCC,
        collections=[],
    )
    response_1 = client.put(
        "/api/v1/families/A.0.0.1",
        json=family_1.model_dump(),
        headers=user_header_token,
    )
    response_2 = client.put(
        "/api/v1/families/A.0.0.2",
        json=family_2.model_dump(),
        headers=user_header_token,
    )

    assert response_1.status_code == status.HTTP_200_OK
    assert response_2.status_code == status.HTTP_200_OK

    update_response_1 = client.put(
        "/api/v1/families/A.0.0.1",
        json=family_1.model_copy(update={"geographies": ["GBR"]}).model_dump(),
        headers=user_header_token,
    )

    assert update_response_1.status_code == status.HTTP_200_OK

    db_family_2 = data_db.query(Family).filter(Family.import_id == "A.0.0.2").one()
    family_2_geographies = [g.value for g in db_family_2.geographies]
    assert set(family_2_geographies) == set(["USA", "AUS"])


def test_update_family_concepts(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="apple",
        summary="just a test",
        geographies=["USA"],
        category=FamilyCategory.UNFCCC,
        collections=["C.0.0.3"],
        concepts=[{"id": "C.0.0.1", "title": "Concept 1"}],
    )
    response = client.put(
        "/api/v1/families/A.0.0.1",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["concepts"] == [
        {
            "id": "C.0.0.1",
            "title": "Concept 1",
        },
    ]

    db_family: Family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.1").one()
    )
    assert db_family.title == "apple"
    assert db_family.description == "just a test"
    assert USA_GEO_ID in [g.id for g in db_family.geographies]
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[0].name) == data["slug"]

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
        geographies=["South Asia"],
        category=FamilyCategory.UNFCCC,
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
    assert data["geographies"] == ["South Asia"]
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

    assert expected_geo.id in [g.id for g in db_family.geographies]
    assert db_family.family_category == "UNFCCC"
    db_slug = (
        data_db.query(Slug)
        .filter(Slug.family_import_id == "A.0.0.1")
        .order_by(Slug.created.desc())
        .all()
    )
    assert len(db_slug) == 2
    assert str(db_slug[0].name).startswith("updated-title")

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
        geographies=["Other"],
        category=FamilyCategory.UNFCCC,
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
    assert data["geographies"] == ["Other"]
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
    assert expected_geo.id in [g.id for g in db_family.geographies]
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[0].name) == "Slug1"

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
        geographies=["Other"],
        category=FamilyCategory.UNFCCC,
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
    assert data["geographies"] == ["Other"]
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
    assert expected_geo.id in [g.id for g in db_family.geographies]
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[0].name) == "Slug1"

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
        geographies=["Other"],
        category=FamilyCategory.UNFCCC,
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
        data_db.query(Geography).filter(Geography.display_value == "Afghanistan").one()
    )
    assert expected_geo.id in [g.id for g in db_family.geographies]
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[0].name) == "Slug1"

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
        geographies=["USA"],
        category=FamilyCategory.UNFCCC,
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
    assert db_family.family_category == "UNFCCC"

    geo_id = (
        data_db.query(Geography.id)
        # TODO: PDCT-1406: Properly implement multi-geography support
        .filter(Geography.value == db_family.geographies[0].value).scalar()
    )
    assert geo_id in [g.id for g in db_family.geographies]


def test_update_family_succeeds_when_user_org_different_to_family_org_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="apple",
        summary="just a test",
        geographies=["USA"],
        category=FamilyCategory.UNFCCC,
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
    assert data["geographies"] == ["USA"]
    assert data["category"] == "UNFCCC"
    assert data["collections"] == ["C.0.0.3"]

    db_family: Family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.1").one()
    )
    assert db_family.title == "apple"
    assert db_family.description == "just a test"
    assert USA_GEO_ID in [g.id for g in db_family.geographies]
    assert db_family.family_category == "UNFCCC"
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.1").all()
    assert len(db_slug) == 1
    assert str(db_slug[0].name) == data["slug"]

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
    assert db_family.family_category == "UNFCCC"

    geo_id = (
        data_db.query(Geography.id)
        # TODO: PDCT-1406: Properly implement multi-geography support
        .filter(Geography.value == db_family.geographies[0].value).scalar()
    )
    assert geo_id in [g.id for g in db_family.geographies]


def test_update_family_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="Updated Title",
        summary="just a test",
        geographies=["USA"],
        category=FamilyCategory.UNFCCC,
    )
    response = client.put("/api/v1/families/A.0.0.2", json=new_family.model_dump())
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_family_idempotent_when_ok(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    expected_family = EXPECTED_FAMILIES[1]
    response = client.put(
        f"/api/v1/families/{expected_family['import_id']}",
        json=expected_family,
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == expected_family["title"]
    assert data["summary"] == expected_family["summary"]
    assert data["geographies"] == expected_family["geographies"]
    assert data["category"] == expected_family["category"]
    db_family: Family = (
        data_db.query(Family)
        .filter(Family.import_id == expected_family["import_id"])
        .one()
    )
    assert db_family.title == expected_family["title"]
    assert db_family.description == expected_family["summary"]
    assert db_family.family_category == expected_family["category"]

    geo_id = (
        data_db.query(Geography.id)
        .filter(Geography.value == expected_family["geography"])
        .scalar()
    )
    assert geo_id in [g.id for g in db_family.geographies]


def test_update_family_rollback(
    client: TestClient, data_db: Session, rollback_family_repo, user_header_token
):
    setup_db(data_db)
    new_family = EXPECTED_FAMILIES[1]
    response = client.put(
        "/api/v1/families/A.0.0.2",
        json=new_family,
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    db_family: Family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.2").one()
    )
    assert db_family.title != "Updated Title"
    assert db_family.description != "just a test"

    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.2").all()
    # Ensure no extra slug was created
    assert len(db_slug) == 1

    db_meta = (
        data_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == "A.0.0.2")
        .all()
    )
    # Ensure no metadata was updated
    assert len(db_meta) == 1
    assert db_meta[0].value == {
        "topic": ["Mitigation"],
        "hazard": [],
        "sector": [],
        "keyword": [],
        "framework": [],
        "instrument": [],
    }
    assert rollback_family_repo.update.call_count == 1


def test_update_family_when_not_found(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_write_dto(
        title="Updated Title",
        summary="just a test",
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
    )
    new_family.geographies = ["UK"]
    response = client.put(
        "/api/v1/families/A.0.0.3",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert (
        data["detail"]
        == "One or more of the following geography values are invalid: UK"
    )


def test_update_family_metadata_if_changed(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A.0.0.2",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    family_data = response.json()
    assert family_data["metadata"] == {
        "topic": ["Mitigation"],
        "hazard": [],
        "sector": [],
        "keyword": [],
        "framework": [],
        "instrument": [],
    }

    expected_meta = {
        "topic": ["Adaptation"],
        "hazard": ["Flood"],
        "sector": [],
        "keyword": [],
        "framework": [],
        "instrument": [],
    }
    family_data["metadata"] = expected_meta
    response = client.put(
        "/api/v1/families/A.0.0.2", json=family_data, headers=user_header_token
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["metadata"] == expected_meta

    metadata: FamilyMetadata = (
        data_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == "A.0.0.2")
        .one()
    )
    assert metadata.value == expected_meta


def test_update_family_returns_error_if_payload_contains_invalid_geography_ids(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A.0.0.2",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    family_data = response.json()
    assert family_data["geography"] == "ZWE"

    family_data["geographies"] = ["AGO", "ZWE", "ABC"]
    response = client.put(
        "/api/v1/families/A.0.0.2", json=family_data, headers=user_header_token
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert (
        data["detail"]
        == "One or more of the following geography values are invalid: AGO, ZWE, ABC"
    )


def test_update_family_updates_geographies_if_changed(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    add_data(
        data_db,
        [
            {
                "import_id": "A.0.0.6",
                "title": "title",
                "summary": "gregarious magazine rub",
                "geography": "ALB",
                "geographies": ["ALB", "AND", "ZWE"],
                "category": "UNFCCC",
                "status": "Created",
                "metadata": {
                    "topic": [],
                    "hazard": [],
                    "sector": [],
                    "keyword": [],
                    "framework": [],
                    "instrument": [],
                },
                "organisation": "CCLW",
                "corpus_import_id": "CCLW.corpus.i00000001.n0000",
                "corpus_title": "CCLW national policies",
                "corpus_type": "Laws and Policies",
                "slug": "Slug6",
                "events": ["E.0.0.1", "E.0.0.2"],
                "published_date": "2018-12-24T04:59:31Z",
                "last_updated_date": "2020-12-24T04:59:31Z",
                "documents": [],
                "collections": ["C.0.0.2"],
                "concepts": [],
            }
        ],
    )
    response = client.get(
        "/api/v1/families/A.0.0.6",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    family_data = response.json()
    assert family_data["geographies"] == ["ALB", "AND", "ZWE"]
    family_data["geographies"] = ["ALB", "AND", "USA"]
    family_data["title"] = "Updated Title"

    response = client.put(
        "/api/v1/families/A.0.0.6", json=family_data, headers=user_header_token
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["geographies"] == ["ALB", "AND", "USA"]
    assert data["title"] == "Updated Title"


def test_update_family_successfully_removes_a_geography(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    add_data(
        data_db,
        [
            {
                "import_id": "A.0.0.6",
                "title": "Title of Albania and Andorran project",
                "summary": "gregarious magazine rub",
                "geography": "ALB",
                "geographies": ["ALB", "AND"],
                "category": "UNFCCC",
                "status": "Created",
                "metadata": {
                    "topic": [],
                    "hazard": [],
                    "sector": [],
                    "keyword": [],
                    "framework": [],
                    "instrument": [],
                },
                "organisation": "CCLW",
                "corpus_import_id": "CCLW.corpus.i00000001.n0000",
                "corpus_title": "CCLW national policies",
                "corpus_type": "Laws and Policies",
                "slug": "Slug6",
                "events": ["E.0.0.1", "E.0.0.2"],
                "published_date": "2018-12-24T04:59:31Z",
                "last_updated_date": "2020-12-24T04:59:31Z",
                "documents": [],
                "collections": ["C.0.0.2"],
                "concepts": [],
            }
        ],
    )
    response = client.get(
        "/api/v1/families/A.0.0.6",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    family_data = response.json()
    assert family_data["geographies"] == ["ALB", "AND"]

    family_data["geographies"] = [
        "ALB",
    ]
    family_data["title"] = "Updated Title of Albanian project"
    response = client.put(
        "/api/v1/families/A.0.0.6", json=family_data, headers=user_header_token
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["geographies"] == ["ALB"]
