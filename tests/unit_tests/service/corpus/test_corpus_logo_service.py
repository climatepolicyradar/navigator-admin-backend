"""Tests for the corpus logo upload functionality."""

from urllib.parse import parse_qs, urlparse

import pytest

from app.errors import ValidationError
from app.service import corpus as corpus_service


def test_get_upload_url_success(corpus_repo_mock, monkeypatch):
    """Test successful generation of upload URL."""

    monkeypatch.setenv("CDN_URL", "https://somecdn.org")
    monkeypatch.setenv("CACHE_BUCKET", "some-cache-bucket")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")

    result = corpus_service.get_upload_url("some_corpus_id")
    assert result is not None
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert "some_corpus_id" in str(result.presigned_upload_url)
    assert "some_corpus_id" in str(result.object_cdn_url)

    # The presigned URL must require a matching Cache-Control header on
    # upload, so a fresh upload can never be served stale by a CDN or
    # browser cache that has no other reason to revalidate a fixed S3 key.
    query_params = parse_qs(urlparse(str(result.presigned_upload_url)).query)
    signed_headers = query_params["X-Amz-SignedHeaders"][0]
    assert "cache-control" in signed_headers.split(";")


def test_get_upload_url_raises_db_error(corpus_repo_mock, monkeypatch):
    monkeypatch.setenv("CDN_URL", "https://somecdn.org")
    monkeypatch.setenv("CACHE_BUCKET", "some-cache-bucket")

    corpus_repo_mock.valid = False
    with pytest.raises(ValidationError) as e:
        corpus_service.get_upload_url("some_dodgy_corpus_id")
    expected_msg = "Corpus 'some_dodgy_corpus_id' not found"
    assert e.value.message == expected_msg
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
