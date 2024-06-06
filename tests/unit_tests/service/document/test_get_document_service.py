import pytest

import app.service.document as doc_service
from app.errors import ValidationError

# --- GET


def test_get(document_repo_mock):
    result = doc_service.get("id.1.2.3")
    assert result is not None
    assert result.import_id == "id.1.2.3"
    assert document_repo_mock.get.call_count == 1


def test_get_returns_none(document_repo_mock):
    document_repo_mock.return_empty = True
    result = doc_service.get("id.1.2.3")
    assert result is None
    assert document_repo_mock.get.call_count == 1


def test_get_raises_when_invalid_id(document_repo_mock):
    with pytest.raises(ValidationError) as e:
        doc_service.get("a.b.c")
    expected_msg = "The import id a.b.c is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.get.call_count == 0
