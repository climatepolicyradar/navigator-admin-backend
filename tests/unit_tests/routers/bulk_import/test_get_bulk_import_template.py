"""
Tests the route for retrieving a bulk import template by corpus.

This uses service mocks and ensures the endpoint calls into each service.
"""

from fastapi import status
from fastapi.testclient import TestClient


def test_bulk_import_template_when_not_authenticated(client: TestClient):
    response = client.get(
        "/api/v1/bulk-import/template/test_corpus_type",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_bulk_import_template_when_non_admin_non_super(
    client: TestClient, user_header_token
):
    response = client.get(
        "/api/v1/bulk-import/template/test_corpus_type", headers=user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_bulk_import_template_when_admin_non_super(
    client: TestClient, admin_user_header_token
):
    response = client.get(
        "/api/v1/bulk-import/template/test_corpus_type", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_bulk_import_template_when_ok(
    client: TestClient, superuser_header_token, db_client_corpus_helpers_mock
):
    response = client.get(
        "/api/v1/bulk-import/template/test_corpus_type",
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "collections": [
            {
                "import_id": {"title": "Import Id", "type": "string"},
                "title": {"title": "Title", "type": "string"},
                "description": {"title": "Description", "type": "string"},
                "metadata": {},
            }
        ],
        "families": [
            {
                "import_id": {"title": "Import Id", "type": "string"},
                "title": {"title": "Title", "type": "string"},
                "summary": {"title": "Summary", "type": "string"},
                "geographies": {
                    "items": {"type": "string"},
                    "title": "Geographies",
                    "type": "array",
                },
                "category": {"title": "Category", "type": "string"},
                "metadata": {
                    "test": {
                        "allow_blanks": False,
                        "allow_any": False,
                        "allowed_values": [],
                    }
                },
                "collections": {
                    "items": {"type": "string"},
                    "title": "Collections",
                    "type": "array",
                },
                "concepts": {
                    "anyOf": [
                        {
                            "items": {"type": "object"},
                            "type": "array",
                        },
                        {"type": "null"},
                    ],
                    "default": [],
                    "title": "Concepts",
                },
            }
        ],
        "documents": [
            {
                "import_id": {"title": "Import Id", "type": "string"},
                "family_import_id": {"title": "Family Import Id", "type": "string"},
                "variant_name": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                    "title": "Variant Name",
                },
                "metadata": {
                    "test": {
                        "allow_blanks": False,
                        "allow_any": False,
                        "allowed_values": [],
                    }
                },
                "title": {"title": "Title", "type": "string"},
                "source_url": {
                    "anyOf": [
                        {"format": "uri", "minLength": 1, "type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "title": "Source Url",
                },
                "user_language_name": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                    "title": "User Language Name",
                },
            }
        ],
        "events": [
            {
                "import_id": {"title": "Import Id", "type": "string"},
                "family_import_id": {"title": "Family Import Id", "type": "string"},
                "family_document_import_id": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                    "title": "Family Document Import Id",
                },
                "event_title": {"title": "Event Title", "type": "string"},
                "date": {"format": "date-time", "title": "Date", "type": "string"},
                "event_type_value": {
                    "allow_blanks": False,
                    "allow_any": False,
                    "allowed_values": [],
                },
                "metadata": {
                    "event_type": {
                        "allow_blanks": False,
                        "allow_any": False,
                        "allowed_values": [],
                    }
                },
            }
        ],
    }
