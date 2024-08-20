"""
Tests the route for retrieving a data ingest template by corpus.

This uses service mocks and ensures the endpoint calls into each service.
"""

from typing import Optional, cast

from db_client.functions.corpus_helpers import TaxonomyData
from fastapi import status
from fastapi.testclient import TestClient

import app.service.taxonomy as taxonomy


def test_ingest_template_when_not_authenticated(client: TestClient):
    response = client.get(
        "/api/v1/ingest/template/test_corpus_type",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ingest_template_when_ok(
    client: TestClient, user_header_token, monkeypatch, mocker
):
    def mock_get_taxonomy_by_corpus_type_name(_, __) -> Optional[TaxonomyData]:
        metadata = {
            "allow_blanks": False,
            "allow_any": False,
            "allowed_values": [],
        }
        return cast(TaxonomyData, {"test": metadata, "_document": {"test": metadata}})

    monkeypatch.setattr(
        taxonomy,
        "get_taxonomy_by_corpus_type_name",
        mock_get_taxonomy_by_corpus_type_name,
    )

    response = client.get(
        "/api/v1/ingest/template/test_corpus_type",
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "collections": [
            {
                "import_id": {"title": "Import Id", "type": "string"},
                "title": {"title": "Title", "type": "string"},
                "description": {"title": "Description", "type": "string"},
            }
        ],
        "families": [
            {
                "import_id": {"title": "Import Id", "type": "string"},
                "title": {"title": "Title", "type": "string"},
                "summary": {"title": "Summary", "type": "string"},
                "geography": {"title": "Geography", "type": "string"},
                "category": {"title": "Category", "type": "string"},
                "metadata": {
                    "test": {
                        "allow_any": False,
                        "allow_blanks": False,
                        "allowed_values": [],
                    },
                },
                "collections": {
                    "items": {"type": "string"},
                    "title": "Collections",
                    "type": "array",
                },
                "events": [
                    {
                        "import_id": {"title": "Import Id", "type": "string"},
                        "event_title": {"title": "Event Title", "type": "string"},
                        "date": {
                            "format": "date-time",
                            "title": "Date",
                            "type": "string",
                        },
                        "event_type_value": {
                            "title": "Event Type Value",
                            "type": "string",
                        },
                        "family_import_id": {
                            "title": "Family Import Id",
                            "type": "string",
                        },
                    }
                ],
                "documents": [
                    {
                        "events": [
                            {
                                "import_id": {"title": "Import Id", "type": "string"},
                                "event_title": {
                                    "title": "Event Title",
                                    "type": "string",
                                },
                                "date": {
                                    "format": "date-time",
                                    "title": "Date",
                                    "type": "string",
                                },
                                "event_type_value": {
                                    "title": "Event Type Value",
                                    "type": "string",
                                },
                                "family_document_import_id": {
                                    "title": "Family Document Import Id",
                                    "anyOf": [{"type": "string"}, {"type": "null"}],
                                    "default": None,
                                },
                            }
                        ],
                        "variant_name": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "default": None,
                            "title": "Variant Name",
                        },
                        "metadata": {
                            "test": {
                                "allow_any": False,
                                "allow_blanks": False,
                                "allowed_values": [],
                            },
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
                            "title": "User Language Name",
                        },
                    }
                ],
            }
        ],
    }
