from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import (
    EXPECTED_CCLW_CORPUS,
    EXPECTED_NUM_CORPORA,
    EXPECTED_UNFCCC_CORPUS,
    setup_db,
)


def test_get_all_corpus_types(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpus-types",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Ensure there are corpus types returned

    assert len(data) == EXPECTED_NUM_CORPORA
    for item in data:
        assert isinstance(item, dict)
        assert all(key in ["name", "description", "metadata"] for key in item)

    # Check Laws and Policies content.
    laws_and_policies_ct = data[1]
    assert laws_and_policies_ct["name"] == EXPECTED_CCLW_CORPUS["corpus_type_name"]
    assert (
        laws_and_policies_ct["description"]
        == EXPECTED_CCLW_CORPUS["corpus_type_description"]
    )
    assert laws_and_policies_ct["metadata"] is not None
    assert isinstance(laws_and_policies_ct["metadata"], dict)

    # Check Intl. Agreements content.
    int_agreements_ct = data[0]
    assert int_agreements_ct["name"] == EXPECTED_UNFCCC_CORPUS["corpus_type_name"]
    assert (
        int_agreements_ct["description"]
        == EXPECTED_UNFCCC_CORPUS["corpus_type_description"]
    )

    assert int_agreements_ct["metadata"] is not None
    assert isinstance(int_agreements_ct["metadata"], dict)


def test_get_all_corpus_types_non_super(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpus-types",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User cclw@cpr.org is not authorised to READ a CORPUS_TYPE"


def test_get_all_corpus_types_when_not_authenticated(
    client: TestClient, data_db: Session
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpus-types",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
