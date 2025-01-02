from db_client.models.organisation import CorpusType
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.corpus_type import create_corpus_type_create_dto
from tests.integration_tests.setup_db import setup_db


def test_create_corpus_type(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    new_ct = create_corpus_type_create_dto("test_ct_name")
    response = client.post(
        "/api/v1/corpus-types",
        json=new_ct.model_dump(),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data == "test_ct_name"

    actual_corpus = data_db.query(CorpusType).filter(CorpusType.name == data).one()

    assert actual_corpus.name == "test_ct_name"
    assert actual_corpus.description == "test_description"
    assert actual_corpus.valid_metadata == {
        "event_type": ["Passed/Approved"],
        "_event": {
            "event_type": ["Passed/Approved"],
            "datetime_event_name": ["Passed/Approved"],
        },
        "_document": {},
    }


def test_create_corpus_type_when_not_authenticated(
    client: TestClient, data_db: Session
):
    setup_db(data_db)
    new_ct = create_corpus_type_create_dto("some-corpus-type")
    response = client.post(
        "/api/v1/corpus-types",
        json=new_ct.model_dump(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_corpus_type_non_admin_non_super(client: TestClient, user_header_token):
    new_ct = create_corpus_type_create_dto("some-corpus-type")
    response = client.post(
        "/api/v1/corpus-types", json=new_ct.model_dump(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"] == "User cclw@cpr.org is not authorised to CREATE a CORPUS_TYPE"
    )


def test_create_corpus_admin_non_super(client: TestClient, admin_user_header_token):
    new_ct = create_corpus_type_create_dto("some-corpus-type")
    response = client.post(
        "/api/v1/corpus-types",
        json=new_ct.model_dump(),
        headers=admin_user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"] == "User admin@cpr.org is not authorised to CREATE a CORPUS_TYPE"
    )
