from typing import cast

from db_client.models.organisation.corpus import Corpus, CorpusType
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.corpus import create_corpus_write_dto
from tests.integration_tests.setup_db import setup_db


def test_update_corpus(client: TestClient, data_db: Session, superuser_header_token):
    setup_db(data_db)
    old_ct = (
        data_db.query(CorpusType).filter(CorpusType.name == "Laws and Policies").one()
    )
    new_corpus = create_corpus_write_dto()
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "title"
    assert data["description"] == "description"
    assert data["corpus_text"] == "corpus_text"
    assert data["corpus_image_url"] == "some-picture.png"
    assert data["organisation_id"] == 1
    assert data["organisation_name"] == "CCLW"
    assert data["corpus_type_name"] == old_ct.name
    assert data["corpus_type_description"] == "some description"
    assert isinstance(data["metadata"], dict)
    assert data["metadata"] == old_ct.valid_metadata

    db_corpus: Corpus = (
        data_db.query(Corpus)
        .filter(Corpus.import_id == "CCLW.corpus.i00000001.n0000")
        .one()
    )
    assert db_corpus.import_id == "CCLW.corpus.i00000001.n0000"
    assert db_corpus.title == "title"
    assert db_corpus.description == "description"
    assert db_corpus.corpus_text == "corpus_text"
    assert db_corpus.corpus_type_name == "Laws and Policies"
    assert db_corpus.corpus_image_url == "some-picture.png"
    assert db_corpus.organisation_id == 1

    ct: CorpusType = (
        data_db.query(CorpusType).filter(CorpusType.name == "Laws and Policies").one()
    )
    assert ct.name == old_ct.name
    assert ct.description == "some description"
    assert ct.valid_metadata == old_ct.valid_metadata


def test_update_corpus_allows_none_corpus_image_url(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    old_ct = (
        data_db.query(CorpusType).filter(CorpusType.name == "Laws and Policies").one()
    )
    new_corpus = create_corpus_write_dto(image_url=None)
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "title"
    assert data["description"] == "description"
    assert data["corpus_text"] == "corpus_text"
    assert data["corpus_image_url"] is None
    assert data["organisation_id"] == 1
    assert data["organisation_name"] == "CCLW"
    assert data["corpus_type_name"] == old_ct.name
    assert data["corpus_type_description"] == "some description"
    assert isinstance(data["metadata"], dict)
    assert data["metadata"] == old_ct.valid_metadata

    db_corpus: Corpus = (
        data_db.query(Corpus)
        .filter(Corpus.import_id == "CCLW.corpus.i00000001.n0000")
        .one()
    )
    assert db_corpus.import_id == "CCLW.corpus.i00000001.n0000"
    assert db_corpus.title == "title"
    assert db_corpus.description == "description"
    assert db_corpus.corpus_text == "corpus_text"
    assert db_corpus.corpus_type_name == "Laws and Policies"
    assert db_corpus.corpus_image_url is None
    assert db_corpus.organisation_id == 1

    ct: CorpusType = (
        data_db.query(CorpusType).filter(CorpusType.name == "Laws and Policies").one()
    )
    assert ct.name == old_ct.name
    assert ct.description == "some description"
    assert ct.valid_metadata == old_ct.valid_metadata


def test_update_corpus_allows_none_corpus_description(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    old_ct = (
        data_db.query(CorpusType).filter(CorpusType.name == "Laws and Policies").one()
    )
    new_corpus = create_corpus_write_dto(description=None)
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "CCLW.corpus.i00000001.n0000"
    assert data["title"] == "title"
    assert data["description"] is None
    assert data["corpus_text"] == "corpus_text"
    assert data["corpus_image_url"] == "some-picture.png"
    assert data["organisation_id"] == 1
    assert data["organisation_name"] == "CCLW"
    assert data["corpus_type_name"] == old_ct.name
    assert data["corpus_type_description"] == "some description"
    assert isinstance(data["metadata"], dict)
    assert data["metadata"] == old_ct.valid_metadata

    db_corpus: Corpus = (
        data_db.query(Corpus)
        .filter(Corpus.import_id == "CCLW.corpus.i00000001.n0000")
        .one()
    )
    assert db_corpus.import_id == "CCLW.corpus.i00000001.n0000"
    assert db_corpus.title == "title"
    assert db_corpus.description is None
    assert db_corpus.corpus_text == "corpus_text"
    assert db_corpus.corpus_type_name == "Laws and Policies"
    assert db_corpus.corpus_image_url == "some-picture.png"
    assert db_corpus.organisation_id == 1

    ct: CorpusType = (
        data_db.query(CorpusType).filter(CorpusType.name == "Laws and Policies").one()
    )
    assert ct.name == old_ct.name
    assert ct.description == "some description"
    assert ct.valid_metadata == old_ct.valid_metadata


def test_update_corpus_allows_none_attribution_url(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    old_ct = (
        data_db.query(CorpusType).filter(CorpusType.name == "Laws and Policies").one()
    )
    new_corpus = create_corpus_write_dto(attribution_url=None)
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["organisation_id"] == 1
    assert data["organisation_name"] == "CCLW"
    assert data["corpus_type_name"] == old_ct.name

    db_corpus: Corpus = (
        data_db.query(Corpus)
        .filter(Corpus.import_id == "CCLW.corpus.i00000001.n0000")
        .one()
    )
    assert db_corpus.attribution_url is None


def test_updates_corpus_attribution_url(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    old_ct = (
        data_db.query(CorpusType).filter(CorpusType.name == "Laws and Policies").one()
    )
    new_corpus = create_corpus_write_dto(
        attribution_url="http://new-attribution-url.com"
    )
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["organisation_id"] == 1
    assert data["organisation_name"] == "CCLW"
    assert data["corpus_type_name"] == old_ct.name
    assert data["attribution_url"] == "http://new-attribution-url.com"

    db_corpus: Corpus = (
        data_db.query(Corpus)
        .filter(Corpus.import_id == "CCLW.corpus.i00000001.n0000")
        .one()
    )
    assert db_corpus.attribution_url == "http://new-attribution-url.com"


def test_update_corpus_when_not_authorised(client: TestClient, data_db: Session):
    setup_db(data_db)
    new_corpus = create_corpus_write_dto()
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000", json=new_corpus.model_dump()
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_corpus_non_super_non_admin(client: TestClient, user_header_token):
    new_corpus = create_corpus_write_dto()
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000",
        json=new_corpus.model_dump(),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User cclw@cpr.org is not authorised to UPDATE a CORPUS"


def test_update_corpus_non_super_admin(client: TestClient, admin_user_header_token):
    new_corpus = create_corpus_write_dto()
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000",
        json=new_corpus.model_dump(),
        headers=admin_user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User admin@cpr.org is not authorised to UPDATE a CORPUS"


def test_update_corpus_idempotent(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    old_corpus, old_ct = (
        data_db.query(Corpus, CorpusType)
        .join(Corpus, Corpus.corpus_type_name == CorpusType.name)
        .filter(CorpusType.name == "Laws and Policies")
        .one()
    )

    new_corpus = create_corpus_write_dto(
        title=old_corpus.title,
        description=old_corpus.description,
        corpus_text=old_corpus.corpus_text,
        image_url=old_corpus.corpus_image_url,
        corpus_type_description="Laws and policies",
    )
    old_corpus = cast(Corpus, old_corpus)
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["import_id"] == old_corpus.import_id
    assert data["title"] == old_corpus.title
    assert data["description"] == old_corpus.description
    assert data["corpus_text"] == old_corpus.corpus_text
    assert data["corpus_image_url"] == old_corpus.corpus_image_url
    assert data["organisation_id"] == old_corpus.organisation_id
    assert data["corpus_type_name"] == old_ct.name
    assert data["corpus_type_description"] == old_ct.description
    assert isinstance(data["metadata"], dict)
    assert data["metadata"] == old_ct.valid_metadata

    db_corpus: Corpus = (
        data_db.query(Corpus)
        .filter(Corpus.import_id == "CCLW.corpus.i00000001.n0000")
        .one()
    )
    assert db_corpus.import_id == old_corpus.import_id
    assert db_corpus.title == old_corpus.title
    assert db_corpus.description == old_corpus.description
    assert db_corpus.corpus_text == old_corpus.corpus_text
    assert db_corpus.corpus_image_url == old_corpus.corpus_image_url
    assert db_corpus.organisation_id == old_corpus.organisation_id
    assert db_corpus.corpus_type_name == old_corpus.corpus_type_name


def test_update_corpus_rollback_when_db_error(
    client: TestClient, data_db: Session, rollback_corpus_repo, superuser_header_token
):
    setup_db(data_db)
    new_corpus = create_corpus_write_dto(title="Updated Title")
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    db_corpus: Corpus = (
        data_db.query(Corpus)
        .filter(Corpus.import_id == "CCLW.corpus.i00000001.n0000")
        .one()
    )
    assert db_corpus.title != "Updated Title"
    assert db_corpus.description != "description"
    assert rollback_corpus_repo.update.call_count == 1


def test_update_corpus_when_not_found(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    new_corpus = create_corpus_write_dto(title="Updated Title")
    response = client.put(
        "/api/v1/corpora/CCLW.corpus.i00000999.n0000",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Corpus not updated: CCLW.corpus.i00000999.n0000"
