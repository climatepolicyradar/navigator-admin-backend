import pytest

import app.service.document as doc_service
from app.errors import RepositoryError, ValidationError
from tests.helpers.document import create_document_write_dto

# --- UPDATE


def test_update(document_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None

    updated_doc = create_document_write_dto()
    result = doc_service.update(document.import_id, updated_doc)
    assert result is not None
    assert document_repo_mock.update.call_count == 1


def test_update_when_missing(document_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.return_empty = True

    updated_doc = create_document_write_dto()
    with pytest.raises(RepositoryError) as e:
        doc_service.update(document.import_id, updated_doc)
    assert e.value.message == "Error when updating document a.b.c.d"
    assert document_repo_mock.update.call_count == 1


def test_update_raises_when_invalid_id(document_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document.import_id = "invalid"

    updated_doc = create_document_write_dto()
    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, updated_doc)
    expected_msg = f"The import id {document.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.update.call_count == 0


def test_update_raises_when_invalid_variant(document_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document.variant_name = ""

    updated_doc = create_document_write_dto(variant_name="")
    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, updated_doc)
    expected_msg = "Variant name is empty"
    assert e.value.message == expected_msg
    assert document_repo_mock.update.call_count == 0
