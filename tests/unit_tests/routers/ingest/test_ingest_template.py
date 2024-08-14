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
        "collections": [
            {
                "title": {"title": "Title", "type": "string"},
                "description": {"title": "Description", "type": "string"},
            }
        ],
        "families": [
            {
                "title": {"title": "Title", "type": "string"},
                "summary": {"title": "Summary", "type": "string"},
                "geography": {"title": "Geography", "type": "string"},
                "category": {"title": "Category", "type": "string"},
                "metadata": {
                    "author": {
                        "allow_any": "false",
                        "allow_blanks": "false",
                        "allowed_values": [
                            "Author One",
                            "Author Two",
                        ],  # these will need updating with real values
                    },
                    "author_type": {
                        "allow_any": "false",
                        "allow_blanks": "false",
                        "allowed_values": [
                            "Type One",
                            "Type Two",
                        ],  # these will need updating with real values
                    },
                    "event_type": {
                        "allow_any": "false",
                        "allow_blanks": "false",
                        "allowed_values": [
                            "Event One",
                            "Event Two",
                        ],  # these will need updating with real values
                    },
                },
                "collections": {
                    "items": {"type": "string"},
                    "title": "Collections",
                    "type": "array",
                },
                "events": [
                    {
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
                    }
                ],
                "documents": [
                    {
                        "events": [
                            {
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
                            }
                        ],
                        "variant_name": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "default": None,
                            "title": "Variant Name",
                        },
                        "metadata": {
                            "role": {
                                "allow_any": "false",
                                "allow_blanks": "false",
                                "allowed_values": [
                                    "Role One",
                                    "Role Two",
                                ],  # these will need updating with real values
                            },
                            "type": {
                                "allow_any": "false",
                                "allow_blanks": "false",
                                "allowed_values": [
                                    "Type One",
                                    "Type Two",
                                ],  # these will need updating with real values
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
