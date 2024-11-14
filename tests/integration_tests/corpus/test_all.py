from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import (
    EXPECTED_CCLW_CORPUS,
    EXPECTED_CORPORA_KEYS,
    EXPECTED_NUM_CORPORA,
    EXPECTED_UNFCCC_CORPUS,
    setup_db,
)


def test_get_all_corpora_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpora",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == EXPECTED_NUM_CORPORA

    for item in data:
        assert set(EXPECTED_CORPORA_KEYS).symmetric_difference(set(item.keys())) == set(
            []
        )
        assert isinstance(item["metadata"], dict)
        assert isinstance(item["organisation_id"], int)
        item = {
            k: v for k, v in item.items() if k not in ["metadata", "organisation_id"]
        }
        assert any(
            corpus == item for corpus in [EXPECTED_CCLW_CORPUS, EXPECTED_UNFCCC_CORPUS]
        )


def test_get_all_corpora_non_super(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpora",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "User cclw@cpr.org is not authorised to READ a CORPORA"


def test_get_all_corpora_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/corpora",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
