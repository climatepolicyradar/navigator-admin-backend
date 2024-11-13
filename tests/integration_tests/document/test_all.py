from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import EXPECTED_DOCUMENTS, setup_db


def test_get_all_documents_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["D.0.0.1", "D.0.0.2", "D.0.0.3"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    sdata = sorted(data, key=lambda d: d["import_id"])
    assert all(field in col for col in sdata for field in ("created", "last_modified"))

    actual_data = [
        {
            k: v
            for k, v in col.items()
            if k not in ("created", "last_modified", "physical_id")
        }
        for col in sdata
    ]
    assert actual_data[0] == EXPECTED_DOCUMENTS[0]
    assert actual_data[1] == EXPECTED_DOCUMENTS[1]
    assert actual_data[2] == EXPECTED_DOCUMENTS[2]


def test_get_all_documents_cclw(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["D.0.0.3"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    sdata = sorted(data, key=lambda d: d["import_id"])
    assert all(field in col for col in sdata for field in ("created", "last_modified"))

    actual_data = [
        {
            k: v
            for k, v in col.items()
            if k not in ("created", "last_modified", "physical_id")
        }
        for col in sdata
    ]
    assert actual_data[0] == EXPECTED_DOCUMENTS[2]


def test_get_all_documents_unfccc(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents",
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["D.0.0.1", "D.0.0.2"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    sdata = sorted(data, key=lambda d: d["import_id"])
    assert all(field in col for col in sdata for field in ("created", "last_modified"))

    actual_data = [
        {
            k: v
            for k, v in col.items()
            if k not in ("created", "last_modified", "physical_id")
        }
        for col in sdata
    ]
    assert actual_data[0] == EXPECTED_DOCUMENTS[0]
    assert actual_data[1] == EXPECTED_DOCUMENTS[1]


def test_get_all_documents_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/documents",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
