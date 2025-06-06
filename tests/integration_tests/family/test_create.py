from typing import Optional

from db_client.models.dfce.collection import CollectionFamily
from db_client.models.dfce.family import (
    Family,
    FamilyCorpus,
    FamilyGeography,
    Geography,
    Slug,
)
from db_client.models.dfce.metadata import FamilyMetadata
from db_client.models.organisation.corpus import Corpus
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.family import create_family_create_dto
from tests.integration_tests.setup_db import setup_db


def test_create_family(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
        collections=["C.0.0.3"],
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    expected_import_id = "CCLW.family.i00000002.n0000"
    assert response.json() == expected_import_id
    actual_family = (
        data_db.query(Family).filter(Family.import_id == expected_import_id).one()
    )

    assert actual_family.title == "Title"
    assert actual_family.description == "test test test"

    actual_geo = (
        data_db.query(Geography)
        .join(FamilyGeography, FamilyGeography.geography_id == Geography.id)
        .filter(FamilyGeography.family_import_id == expected_import_id)
        .one()
    )
    assert actual_geo.value == "CHN"
    metadata = (
        data_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == expected_import_id)
        .one()
    )
    assert metadata.value is not None
    assert metadata.value == {
        "topic": [],
        "hazard": [],
        "sector": [],
        "keyword": [],
        "framework": [],
        "instrument": [],
    }

    db_collection: Optional[list[CollectionFamily]] = (
        data_db.query(CollectionFamily)
        .filter(CollectionFamily.family_import_id == expected_import_id)
        .all()
    )
    assert db_collection is not None
    assert len(db_collection) == 1
    assert db_collection[0].collection_import_id == "C.0.0.3"

    # New schema tests.
    fc = (
        data_db.query(FamilyCorpus)
        .filter(FamilyCorpus.family_import_id == expected_import_id)
        .all()
    )
    assert len(fc) == 1
    assert fc[-1].corpus_import_id is not None
    corpus = (
        data_db.query(Corpus)
        .filter(Corpus.import_id == fc[-1].corpus_import_id)
        .one_or_none()
    )
    assert corpus is not None


def test_create_family_when_not_authorised(client: TestClient, data_db: Session):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
    )
    response = client.post(
        "/api/v1/families",
        json=new_family.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_family_rollback(
    client: TestClient, data_db: Session, rollback_family_repo, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    actual_family = (
        data_db.query(Family).filter(Family.import_id == "A.0.0.9").one_or_none()
    )
    assert actual_family is None
    db_slug = data_db.query(Slug).filter(Slug.family_import_id == "A.0.0.9").all()
    # Ensure no slug was created
    assert len(db_slug) == 0
    assert rollback_family_repo.create.call_count == 1


def test_create_family_when_db_error(
    client: TestClient, data_db: Session, bad_family_repo, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_family_repo.create.call_count == 1


def test_create_family_when_invalid_geo(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
    )
    new_family.geographies = ["UK"]
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert (
        data["detail"]
        == "One or more of the following geography values are invalid: UK"
    )


def test_create_family_when_invalid_category(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
    )
    new_family.category = "invalid"
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Invalid is not a valid FamilyCategory"


def test_create_family_when_invalid_collection_id(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
        collections=["col1"],
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "The import ids are invalid: ['col1']"


def test_create_family_when_invalid_collection_org(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
        collections=["C.0.0.1"],
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"]
        == "Organisation mismatch between some collections and the current user"
    )


def test_create_family_when_invalid_metadata_cclw(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
        metadata={"color": ["pink"], "size": ["0"]},
    )
    response = client.post(
        "/api/v1/families",
        json=new_family.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()

    key_text = "{'topic', 'hazard', 'sector', 'keyword', 'framework', 'instrument'}"

    expected_message = "Metadata validation failed: "
    expected_missing_message = f"Missing metadata keys: {key_text}"
    expected_extra_message = f"Extra metadata keys: {list(new_family.metadata.keys())}"

    assert data["detail"].startswith(expected_message)
    assert len(data["detail"]) == len(expected_message) + len(
        expected_missing_message
    ) + len(expected_extra_message) + len(",")


def test_create_family_when_invalid_metadata_unfccc(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
        metadata={"color": ["pink"], "size": ["0"]},
        corpus_import_id="UNFCCC.corpus.i00000001.n0000",
    )
    response = client.post(
        "/api/v1/families",
        json=new_family.model_dump(),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()

    key_text = "{'author_type', 'author'}"

    expected_message = "Metadata validation failed: "
    expected_missing_message = f"Missing metadata keys: {key_text}"
    expected_extra_message = f"Extra metadata keys: {list(new_family.metadata.keys())}"
    assert data["detail"].startswith(expected_message)
    assert len(data["detail"]) == len(expected_message) + len(
        expected_missing_message
    ) + len(expected_extra_message) + len(",")


def test_create_family_when_org_mismatch(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
        metadata={"author": ["CPR"], "author_type": ["Party"]},
        corpus_import_id="UNFCCC.corpus.i00000001.n0000",
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"]
        == "User 'cclw@cpr.org' is not authorised to perform operation on 'UNFCCC.corpus.i00000001.n0000'"
    )


def test_create_endpoint_creates_family_with_multiple_geographies(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Test Title",
        summary="test test test",
        geography="ALB",
        geographies=["ALB", "BRB", "BHS"],
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    expected_import_id = "CCLW.family.i00000002.n0000"
    assert response.json() == expected_import_id
    actual_family = (
        data_db.query(Family).filter(Family.import_id == expected_import_id).one()
    )

    assert actual_family.title == "Test Title"

    actual_geos = (
        data_db.query(Geography)
        .join(FamilyGeography, FamilyGeography.geography_id == Geography.id)
        .filter(FamilyGeography.family_import_id == expected_import_id)
        .all()
    )
    assert len(actual_geos) == 3
    assert set([geo.value for geo in actual_geos]) == {"ALB", "BHS", "BRB"}
