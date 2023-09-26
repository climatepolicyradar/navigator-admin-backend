from typing import cast
import pytest
from app.model.document import DocumentReadDTO, DocumentWriteDTO
import app.service.document as doc_service
from app.errors import ValidationError
from unit_tests.mocks.repos.document_repo import create_document_dto as create_dto


def _to_write_dto(dto: DocumentReadDTO) -> DocumentWriteDTO:
    return cast(DocumentWriteDTO, dto)


def test_document_service_get_upload_details(test_s3_client):
    result = doc_service.get_upload_details("path/file.ext", True)
    assert result is not None
    assert len(result) == 2
    # Check the signed url starts with the right path
    assert result[0].startswith(
        "https://test-document-bucket.s3.amazonaws.com/path/file.ext?"
    )
    assert "X-Amz-Algorithm" in result[0]
    assert "X-Amz-Credential" in result[0]
    assert "X-Amz-Date" in result[0]
    assert "X-Amz-Expires=3600" in result[0]
    assert "X-Amz-Signature" in result[0]

    assert result[1] == "https://cdn.climatepolicyradar.org/path/file.ext"


# --- GET


def test_get(document_repo_mock):
    result = doc_service.get("id.1.2.3")
    assert result is not None
    assert result.import_id == "id.1.2.3"
    assert document_repo_mock.get.call_count == 1


def test_get_returns_none(document_repo_mock):
    document_repo_mock.return_empty = True
    result = doc_service.get("id.1.2.3")
    assert result is not None
    assert document_repo_mock.get.call_count == 1


def test_get_raises_when_invalid_id(document_repo_mock):
    with pytest.raises(ValidationError) as e:
        doc_service.get("a.b.c")
    expected_msg = "The import id a.b.c is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.get.call_count == 0


# --- SEARCH


def test_search(document_repo_mock):
    result = doc_service.search("two")
    assert result is not None
    assert len(result) == 1
    assert document_repo_mock.search.call_count == 1


def test_search_when_missing(document_repo_mock):
    document_repo_mock.return_empty = True
    result = doc_service.search("empty")
    assert result is not None
    assert len(result) == 0
    assert document_repo_mock.search.call_count == 1


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


# --- UPDATE


def test_update(
    document_repo_mock,
):
    document = doc_service.get("a.b.c.d")
    assert document is not None

    result = doc_service.update(_to_write_dto(document))
    assert result is not None
    assert document_repo_mock.update.call_count == 1


def test_update_when_missing(
    document_repo_mock,
):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.return_empty = True

    result = doc_service.update(_to_write_dto(document))
    assert result is None
    assert document_repo_mock.update.call_count == 1


def test_update_raises_when_invalid_id(
    document_repo_mock,
):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document.import_id = "invalid"

    with pytest.raises(ValidationError) as e:
        doc_service.update(_to_write_dto(document))
    expected_msg = f"The import id {document.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.update.call_count == 0


# --- CREATE


def test_create(document_repo_mock, family_repo_mock):
    new_document = create_dto(import_id="A.0.0.5")
    document = doc_service.create(_to_write_dto(new_document))
    assert document is not None
    assert document_repo_mock.create.call_count == 1
    assert family_repo_mock.get.call_count == 1


def test_create_when_db_fails(document_repo_mock, family_repo_mock):
    new_document = create_dto(import_id="a.b.c.d")
    document_repo_mock.return_empty = True
    document = doc_service.create(_to_write_dto(new_document))
    assert document is None
    assert document_repo_mock.create.call_count == 1
    assert family_repo_mock.get.call_count == 1


def test_create_raises_when_invalid_id(document_repo_mock):
    new_document = create_dto(import_id="invalid")
    with pytest.raises(ValidationError) as e:
        doc_service.create(_to_write_dto(new_document))
    expected_msg = f"The import id {new_document.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.create.call_count == 0


def test_create_raises_when_invalid_family_id(document_repo_mock):
    new_document = create_dto(import_id="a.b.c.d", family_import_id="invalid family")
    with pytest.raises(ValidationError) as e:
        doc_service.create(_to_write_dto(new_document))
    expected_msg = f"The import id {new_document.family_import_id} is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.create.call_count == 0
