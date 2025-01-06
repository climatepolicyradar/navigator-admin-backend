import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import (
    EXPECTED_CCLW_CORPUS,
    EXPECTED_CORPORA_KEYS,
    EXPECTED_UNFCCC_CORPUS,
    setup_db,
)


@pytest.mark.parametrize(
    "expected_corpus",
    [
        EXPECTED_UNFCCC_CORPUS,
        EXPECTED_CCLW_CORPUS,
    ],
)
def test_get_corpus(
    client: TestClient, data_db: Session, superuser_header_token, expected_corpus
):
    setup_db(data_db)
    response = client.get(
        f"/api/v1/corpora/{expected_corpus['import_id']}",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert set(EXPECTED_CORPORA_KEYS).symmetric_difference(set(data.keys())) == set([])
    assert isinstance(data["metadata"], dict)
    assert isinstance(data["organisation_id"], int)
    data = {k: v for k, v in data.items() if k not in ["metadata", "organisation_id"]}
    assert data == expected_corpus


def test_get_corpus_non_super(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpora/UNFCCC.corpus.i00000001.n0000", headers=user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User cclw@cpr.org is not authorised to READ a CORPUS"


def test_get_corpus_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpora/UNFCCC.corpus.i00000001.n0000",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_corpus_when_not_found(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpora/CCLW.corpus.i00000999.n0000",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Corpus not found: CCLW.corpus.i00000999.n0000"


def test_get_corpus_when_id_invalid(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpora/A008",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    expected_msg = "The import id A008 is invalid!"
    assert data["detail"] == expected_msg
