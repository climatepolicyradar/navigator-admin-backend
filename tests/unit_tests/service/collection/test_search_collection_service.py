import pytest

import app.service.collection as collection_service
from app.errors import RepositoryError

# --- SEARCH


def test_search(collection_repo_mock):
    result = collection_service.search({"q": "two"})
    assert result is not None
    assert len(result) == 1
    assert collection_repo_mock.search.call_count == 1


def test_search_db_error(collection_repo_mock):
    collection_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        collection_service.search({"q": "error"})
    assert collection_repo_mock.search.call_count == 1


def test_search_request_timeout(collection_repo_mock):
    collection_repo_mock.throw_timeout_error = True
    with pytest.raises(TimeoutError):
        collection_service.search({"q": "timeout"})
    assert collection_repo_mock.search.call_count == 1


def test_search_missing(collection_repo_mock):
    collection_repo_mock.return_empty = True
    result = collection_service.search({"q": "empty"})
    assert result is not None
    assert len(result) == 0
    assert collection_repo_mock.search.call_count == 1
