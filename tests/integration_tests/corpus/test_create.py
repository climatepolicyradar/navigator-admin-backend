from db_client.models.organisation.corpus import Corpus
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.corpus import create_corpus_create_dto
from tests.integration_tests.setup_db import setup_db


def test_create_corpus(client: TestClient, data_db: Session, superuser_header_token):
    setup_db(data_db)
    new_corpus = create_corpus_create_dto("Laws and Policies")
    response = client.post(
        "/api/v1/corpora",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data == "CCLW.corpus.i00000002.n0000"
    actual_corpus = data_db.query(Corpus).filter(Corpus.import_id == data).one()

    assert actual_corpus.import_id == "CCLW.corpus.i00000002.n0000"
    assert actual_corpus.title == "title"
    assert actual_corpus.description == "description"
    assert actual_corpus.corpus_text == "corpus_text"
    assert actual_corpus.corpus_type_name == "Laws and Policies"
    assert actual_corpus.corpus_image_url == "some-picture.png"
    assert actual_corpus.organisation_id == 1

    ct: int = (
        data_db.query(Corpus)
        .filter(Corpus.corpus_type_name == "Laws and Policies")
        .count()
    )
    assert ct > 1


def test_create_corpus_allows_none_corpus_text(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    new_corpus = create_corpus_create_dto("Laws and Policies", corpus_text=None)
    response = client.post(
        "/api/v1/corpora",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data == "CCLW.corpus.i00000002.n0000"
    actual_corpus = data_db.query(Corpus).filter(Corpus.import_id == data).one()

    assert actual_corpus.import_id == "CCLW.corpus.i00000002.n0000"
    assert actual_corpus.title == "title"
    assert actual_corpus.description == "description"
    assert actual_corpus.corpus_text is None
    assert actual_corpus.corpus_type_name == "Laws and Policies"
    assert actual_corpus.corpus_image_url == "some-picture.png"
    assert actual_corpus.organisation_id == 1

    ct: int = (
        data_db.query(Corpus)
        .filter(Corpus.corpus_type_name == "Laws and Policies")
        .count()
    )
    assert ct > 1


def test_create_corpus_allows_none_corpus_image_url(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    new_corpus = create_corpus_create_dto("Laws and Policies", image_url=None)
    response = client.post(
        "/api/v1/corpora",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data == "CCLW.corpus.i00000002.n0000"
    actual_corpus = data_db.query(Corpus).filter(Corpus.import_id == data).one()

    assert actual_corpus.import_id == "CCLW.corpus.i00000002.n0000"
    assert actual_corpus.title == "title"
    assert actual_corpus.description == "description"
    assert actual_corpus.corpus_text == "corpus_text"
    assert actual_corpus.corpus_type_name == "Laws and Policies"
    assert actual_corpus.corpus_image_url is None
    assert actual_corpus.organisation_id == 1

    ct: int = (
        data_db.query(Corpus)
        .filter(Corpus.corpus_type_name == "Laws and Policies")
        .count()
    )
    assert ct > 1


def test_create_corpus_when_corpus_type_not_exist(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    new_corpus = create_corpus_create_dto(
        "some corpus type", title="test corpus", description="test test test"
    )
    response = client.post(
        "/api/v1/corpora",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert data["detail"] == "Invalid corpus type name"

    actual_corpus = (
        data_db.query(Corpus)
        .filter(Corpus.corpus_type_name == "some corpus type")
        .one_or_none()
    )
    assert actual_corpus is None


def test_create_corpus_when_org_id_not_exist(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    new_corpus = create_corpus_create_dto("Laws and Policies", org_id=100)
    response = client.post(
        "/api/v1/corpora",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert data["detail"] == "Invalid organisation"

    actual_corpus = (
        data_db.query(Corpus).filter(Corpus.organisation_id == 100).one_or_none()
    )
    assert actual_corpus is None


def test_create_corpus_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    new_corpus = create_corpus_create_dto("some-corpus-type")
    response = client.post(
        "/api/v1/corpora",
        json=new_corpus.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_corpus_non_admin_non_super(client: TestClient, user_header_token):
    new_corpus = create_corpus_create_dto("some-corpus-type")
    response = client.post(
        "/api/v1/corpora", json=new_corpus.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User cclw@cpr.org is not authorised to CREATE a CORPORA"


def test_create_corpus_admin_non_super(client: TestClient, admin_user_header_token):
    new_corpus = create_corpus_create_dto("some-corpus-type")
    response = client.post(
        "/api/v1/corpora", json=new_corpus.model_dump(), headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User admin@cpr.org is not authorised to CREATE a CORPORA"


def test_create_corpus_rollback(
    client: TestClient, data_db: Session, rollback_corpus_repo, superuser_header_token
):
    setup_db(data_db)
    new_corpus = create_corpus_create_dto("Laws and Policies")
    response = client.post(
        "/api/v1/corpora",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    actual_corpus = (
        data_db.query(Corpus).filter(Corpus.import_id == "A.0.0.9").one_or_none()
    )
    assert actual_corpus is None
    assert rollback_corpus_repo.create.call_count == 1


def test_create_corpus_when_db_error(
    client: TestClient, data_db: Session, bad_corpus_repo, superuser_header_token
):
    setup_db(data_db)
    new_corpus = create_corpus_create_dto("Laws and Policies")
    response = client.post(
        "/api/v1/corpora",
        json=new_corpus.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_corpus_repo.create.call_count == 1
