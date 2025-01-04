import logging

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import EXPECTED_CORPORA_KEYS, setup_db


@pytest.mark.parametrize(
    "expected_corpus_org_name",
    [
        "UNFCCC",
        "CCLW",
    ],
)
def test_search_corpus_super(
    client: TestClient,
    data_db: Session,
    superuser_header_token,
    expected_corpus_org_name: str,
):
    setup_db(data_db)
    response = client.get(
        f"/api/v1/corpora/?q={expected_corpus_org_name}",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    ids_found = set([f["import_id"] for f in data])
    expected_ids = set([f"{expected_corpus_org_name}.corpus.i00000001.n0000"])
    assert ids_found.symmetric_difference(expected_ids) == set([])

    org_names_found = set([f["organisation_name"] for f in data])
    expected_org_names = set([expected_corpus_org_name])
    assert org_names_found.symmetric_difference(expected_org_names) == set([])

    for item in data:
        assert set(EXPECTED_CORPORA_KEYS).symmetric_difference(set(item.keys())) == set(
            []
        )


def test_search_corpus_non_super(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpora/?q=title",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User cclw@cpr.org is not authorised to READ a CORPUS"


def test_search_corpus_when_not_authorised(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpora/?q=orange",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_search_corpus_when_nothing_found(
    client: TestClient, data_db: Session, superuser_header_token, caplog
):
    setup_db(data_db)
    with caplog.at_level(logging.INFO):
        response = client.get(
            "/api/v1/corpora/?q=chicken",
            headers=superuser_header_token,
        )
    assert response.status_code == status.HTTP_200_OK
    assert (
        "Corpora not found for terms: {'q': 'chicken', 'max_results': 500}"
        in caplog.text
    )


@pytest.mark.parametrize(
    "org_name, corpus_import_id",
    [
        (
            "UNFCCC",
            "UNFCCC.corpus.i00000001.n0000",
        ),
        (
            "CCLW",
            "CCLW.corpus.i00000001.n0000",
        ),
    ],
)
def test_search_corpus_with_max_results(
    client: TestClient,
    data_db: Session,
    superuser_header_token,
    org_name: str,
    corpus_import_id: str,
):
    setup_db(data_db)
    response = client.get(
        f"/api/v1/corpora/?q={org_name}&max_results=1",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    assert len(data) == 1

    ids_found = set([f["import_id"] for f in data])
    expected_ids = set([corpus_import_id])
    assert ids_found.symmetric_difference(expected_ids) == set([])

    for item in data:
        assert set(EXPECTED_CORPORA_KEYS).symmetric_difference(set(item.keys())) == set(
            []
        )


def test_search_corpus_when_invalid_params(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpora/?wrong=param",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"
