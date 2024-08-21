from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_ingest_collections_when_ok(
    test_db: Session, client: TestClient, user_header_token
):

    response = client.post(
        "/api/v1/ingest",
        files={"new_data": open("tests/unit_tests/routers/ingest/test.json", "rb")},
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "collections": ["test.new.collection.0", "test.new.collection.1"]
    }
