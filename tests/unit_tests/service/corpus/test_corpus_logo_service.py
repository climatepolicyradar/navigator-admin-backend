"""Tests for the corpus logo upload functionality."""

import pytest

from app.errors import ValidationError
from app.service import corpus as corpus_service


def test_get_upload_url_success(corpus_repo_mock):
    """Test successful generation of upload URL."""
    result = corpus_service.get_upload_url("some_corpus_id")
    assert result is not None
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert "some_corpus_id" in str(result.presigned_upload_url)
    assert "some_corpus_id" in str(result.cdn_url)


def test_get_upload_url_raises_db_error(corpus_repo_mock):
    corpus_repo_mock.valid = False
    with pytest.raises(ValidationError) as e:
        corpus_service.get_upload_url("some_dodgy_corpus_id")
    expected_msg = "Corpus 'some_dodgy_corpus_id' not found"
    assert e.value.message == expected_msg
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
