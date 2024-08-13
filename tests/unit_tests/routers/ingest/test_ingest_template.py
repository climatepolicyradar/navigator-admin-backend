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
    assert response.json() == {"title": "", "description": ""}
