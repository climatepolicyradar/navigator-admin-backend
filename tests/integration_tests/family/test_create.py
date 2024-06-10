from typing import Optional

from db_client.models.dfce.collection import CollectionFamily
from db_client.models.dfce.family import Family, FamilyCorpus, Slug
from db_client.models.dfce.metadata import FamilyMetadata
from db_client.models.organisation.corpus import Corpus
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.family import create_family_create_dto
from tests.integration_tests.setup_db import setup_db


def test_create_family(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    test_meta = {"color": ["blue"], "size": [888]}
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
        metadata=test_meta,
        collections=["C.0.0.3"],
    )
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_201_CREATED
    expected_import_id = "CCLW.family.i00000001.n0000"
    assert response.json() == expected_import_id
    actual_family = (
        data_db.query(Family).filter(Family.import_id == expected_import_id).one()
    )

    assert actual_family.title == "Title"
    assert actual_family.description == "test test test"

    metadata = (
        data_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == expected_import_id)
        .one()
    )
    assert metadata.value is not None
    assert metadata.value == test_meta

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
    test_meta = {"color": "blue", "size": 888}
    new_family = create_family_create_dto(
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
    client: TestClient, data_db: Session, rollback_family_repo, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
        metadata={"color": ["pink"], "size": [0]},
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
        metadata={"color": ["pink"], "size": [0]},
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
    new_family.geography = "UK"
    response = client.post(
        "/api/v1/families", json=new_family.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "The geography value UK is invalid!"


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
        metadata={"color": ["pink"], "size": [0]},
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
        metadata={"color": ["pink"], "size": [0]},
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


def test_create_family_when_invalid_metadata(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
        metadata={"color": ["pink"], "size": [0]},
        corpus_import_id="UNFCCC.corpus.i00000001.n0000",
    )
    response = client.post(
        "/api/v1/families",
        json=new_family.model_dump(),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    expected_set = set({"author", "author_type"})
    assert data["detail"] == f"Values for the following are missing: {expected_set}"


def test_create_family_when_invalid_corpus_org(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_family = create_family_create_dto(
        title="Title",
        summary="test test test",
        metadata={"author_type": "", "author": ""},
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
