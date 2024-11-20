import io
import json
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.ingest import (
    build_json_file,
    custom_collection,
    custom_document,
    custom_event,
    custom_family,
    default_collection,
    default_document,
    default_event,
)


def create_input_json_with_two_of_each_entity():
    return build_json_file(
        {
            "collections": [
                default_collection,
                custom_collection({"import_id": "test.new.collection.1"}),
            ],
            "families": [
                custom_family({"metadata": {"color": ["blue"], "size": []}}),
                custom_family(
                    {
                        "import_id": "test.new.family.1",
                        "collections": ["test.new.collection.1"],
                        "metadata": {"color": ["blue"], "size": []},
                    }
                ),
            ],
            "documents": [
                custom_document({"metadata": {"color": ["pink"], "size": []}}),
                custom_document(
                    {
                        "import_id": "test.new.document.1",
                        "family_import_id": "test.new.family.1",
                        "metadata": {"color": ["pink"], "size": []},
                    }
                ),
            ],
            "events": [
                default_event,
                custom_event(
                    {
                        "import_id": "test.new.event.1",
                        "family_import_id": "test.new.family.1",
                    }
                ),
            ],
        }
    )


def test_ingest_when_not_authenticated(client: TestClient):
    response = client.post("/api/v1/ingest/test")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ingest_when_non_admin_non_super(client: TestClient, user_header_token):
    response = client.post("/api/v1/ingest/test", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_ingest_when_admin_non_super(client: TestClient, admin_user_header_token):
    response = client.post("/api/v1/ingest/test", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_ingest_data_when_ok(client: TestClient, superuser_header_token):
    corpus_import_id = "test"
    input_json = create_input_json_with_two_of_each_entity()

    with patch("fastapi.BackgroundTasks.add_task") as background_task_mock:
        response = client.post(
            f"/api/v1/ingest/{corpus_import_id}",
            files={"new_data": input_json},
            headers=superuser_header_token,
        )

    background_task_mock.assert_called_once()

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        "message": "Bulk import request accepted. Check Cloudwatch logs for result."
    }


def test_ingest_when_no_data(
    client: TestClient,
    superuser_header_token,
    collection_repo_mock,
    corpus_service_mock,
    basic_s3_client,
):
    test_data = json.dumps({}).encode("utf-8")
    test_data_file = io.BytesIO(test_data)
    response = client.post(
        "/api/v1/ingest/test",
        files={"new_data": test_data_file},
        headers=superuser_header_token,
    )

    assert collection_repo_mock.create.call_count == 0

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_ingest_documents_when_no_family(client: TestClient, superuser_header_token):
    json_input = build_json_file({"documents": [default_document]})

    response = client.post(
        "/api/v1/ingest/test",
        files={"new_data": json_input},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("detail") == "No entity with id test.new.family.0 found"
