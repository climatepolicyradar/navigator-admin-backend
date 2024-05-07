import pytest

import app.service.document as doc_service
from app.errors import ValidationError

# --- DELETE


def test_delete(document_repo_mock):
    ok = doc_service.delete("a.b.c.d")
    assert ok
    assert document_repo_mock.delete.call_count == 1


def test_delete_when_missing(document_repo_mock):
    document_repo_mock.return_empty = True
    ok = doc_service.delete("a.b.c.d")
    assert not ok
    assert document_repo_mock.delete.call_count == 1


def test_delete_raises_when_invalid_id(document_repo_mock):
    import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        doc_service.delete(import_id)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.delete.call_count == 0
