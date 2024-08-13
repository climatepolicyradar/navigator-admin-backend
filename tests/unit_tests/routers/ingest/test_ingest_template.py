"""
Tests the route for retrieving a data ingest template by corpus.

This uses service mocks and ensures the endpoint calls into each service.
"""

from fastapi import status
from fastapi.testclient import TestClient


def test_ingest_template_when_not_authenticated(client: TestClient):
    response = client.get(
        "/api/v1/ingest/template/test_corpus_type",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ingest_template_when_ok(client: TestClient, user_header_token):

    response = client.get(
        "/api/v1/ingest/template/test_corpus_type",
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "collections": [{"title": "", "description": ""}],
        "families": [
            {
                "title": "",
                "summary": "",
                "geography": "",
                "category": "",
                "metadata": "",  # taxonomy?? - valid_metadata on corpus_type?
                "collections": "",  # can we use title to look up the id??
                # "corpus_import_id": "pre-populated based on corpus type?",
                # "organisation": "add manually? - doesn't exist on the create DTO"
                # "events": [
                #     {
                # "event_title": "",
                # "date": "",
                # "event_type_value": "",
                # "family_import_id": "autogenerate",
                # "family_document_import_id": "optional - does this link back to document?",
                #     }
                # ],
                # "documents": [
                #     {
                # "family_import_id": "autogenerate",
                # "variant_name": "optional",
                # "metadata": {
                #     "?": ""
                # },  # taxonomy?? is this the same as families metadata?
                # "title": "",
                # "source_url": "optional",
                # "user_language_name": "optional",
                #         # "events": ["can we use title to look up the id??"],
                #     }
                # ],
            }
        ],
    }
