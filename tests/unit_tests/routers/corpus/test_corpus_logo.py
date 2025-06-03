"""Tests for the corpus logo upload functionality."""

from fastapi import status
from fastapi.testclient import TestClient


def test_get_upload_url_success(
    client: TestClient, superuser_header_token, corpus_service_mock
):
    """Test successful generation of upload URL."""
    response = client.post(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000/upload-url",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "presigned_upload_url" in data
    assert "cdn_url" in data
    assert data["presigned_upload_url"].startswith("https://")
    assert data["cdn_url"].startswith("https://")


def test_get_upload_url_when_not_authenticated(client: TestClient):
    response = client.post(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000/upload-url",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_upload_url_when_non_admin_non_super(client: TestClient, user_header_token):
    response = client.post(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000/upload-url",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_upload_url_when_admin_non_super(
    client: TestClient, admin_user_header_token
):
    response = client.post(
        "/api/v1/corpora/CCLW.corpus.i00000001.n0000/upload-url",
        headers=admin_user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_upload_url_invalid_corpus_id(
    client: TestClient, superuser_header_token, corpus_service_mock
):
    """Test handling of invalid corpus IDs."""
    corpus_service_mock.invalid_corpus_id = True
    response = client.post(
        "/api/v1/corpora/invalid-corpus-id/upload-url",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "Corpus not found" in data["detail"]
