import io
import json

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_ingest_when_corpus_import_id_invalid(
    test_db: Session, client: TestClient, user_header_token
):
    invalid_corpus = "test"
    response = client.post(
        f"/api/v1/ingest/{invalid_corpus}",
        files={"new_data": open("tests/unit_tests/routers/ingest/test.json", "rb")},
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json().get("detail")
        == f"No organisation associated with corpus {invalid_corpus}"
    )


def test_ingest_collections_when_ok(
    test_db: Session, client: TestClient, user_header_token
):

    response = client.post(
        "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
        files={"new_data": open("tests/unit_tests/routers/ingest/test.json", "rb")},
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "collections": ["test.new.collection.0", "test.new.collection.1"]
    }


def test_ingest_collections_when_import_id_empty(
    test_db: Session, client: TestClient, user_header_token
):

    test_data = json.dumps(
        {
            "collections": [
                {
                    "import_id": "",
                    "title": "Test title",
                    "description": "Test description",
                }
            ]
        }
    ).encode("utf-8")
    test_data_file = io.BytesIO(test_data)

    response = client.post(
        "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
        files={"new_data": test_data_file},
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"collections": ["UNFCCC.collection.i00000001.n0000"]}


def test_ingest_collections_when_no_import_id(
    test_db: Session, client: TestClient, user_header_token
):

    test_data = json.dumps(
        {
            "collections": [
                {
                    "title": "Test title",
                    "description": "Test description",
                }
            ]
        }
    ).encode("utf-8")
    test_data_file = io.BytesIO(test_data)

    response = client.post(
        "/api/v1/ingest/UNFCCC.corpus.i00000001.n0000",
        files={"new_data": test_data_file},
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"collections": ["UNFCCC.collection.i00000001.n0000"]}
