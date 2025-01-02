import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import (
    EXPECTED_CCLW_CORPUS,
    EXPECTED_UNFCCC_CORPUS,
    setup_db,
)

EXPECTED_CORPUS_TYPE_KEYS = ["name", "description", "valid_metadata"]


@pytest.mark.parametrize(
    "expected_corpus_type",
    [EXPECTED_CCLW_CORPUS, EXPECTED_UNFCCC_CORPUS],
)
def test_get_corpus_type(
    client: TestClient, data_db: Session, superuser_header_token, expected_corpus_type
):
    setup_db(data_db)
    response = client.get(
        f"/api/v1/corpus-types/{expected_corpus_type['corpus_type_name']}",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert set(EXPECTED_CORPUS_TYPE_KEYS).symmetric_difference(set(data.keys())) == set(
        []
    )

    assert data["name"] == expected_corpus_type["corpus_type_name"]
    assert data["description"] == expected_corpus_type["corpus_type_description"]
    assert data["valid_metadata"] is not None
    assert isinstance(data["valid_metadata"], dict)


def test_get_corpus_type_non_super(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpus-types/SomeCorpusType", headers=user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User cclw@cpr.org is not authorised to READ a CORPUS TYPE"


def test_get_corpus_type_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpus-types/SomeCorpusType",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_corpus_type_when_not_found(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpus-types/NonExistentType",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Corpus type with name NonExistentType not found."
