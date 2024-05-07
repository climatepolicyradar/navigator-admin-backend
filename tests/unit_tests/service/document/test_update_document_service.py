import pytest

import app.service.document as doc_service
from app.errors import RepositoryError, ValidationError
from app.model.document import DocumentReadDTO, DocumentWriteDTO


def _to_write_dto(dto: DocumentReadDTO) -> DocumentWriteDTO:
    return DocumentWriteDTO(
        variant_name=dto.variant_name,
        role=dto.role,
        type=dto.type,
        title=dto.title,
        source_url=dto.source_url,
        user_language_name=dto.user_language_name,
    )


# --- UPDATE


def test_update(
    document_repo_mock,
):
    document = doc_service.get("a.b.c.d")
    assert document is not None

    result = doc_service.update(document.import_id, _to_write_dto(document))
    assert result is not None
    assert document_repo_mock.update.call_count == 1


def test_update_when_missing(
    document_repo_mock,
):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.return_empty = True

    with pytest.raises(RepositoryError) as e:
        doc_service.update(document.import_id, _to_write_dto(document))
    assert e.value.message == "Error when updating document a.b.c.d"
    assert document_repo_mock.update.call_count == 1


def test_update_raises_when_invalid_id(
    document_repo_mock,
):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document.import_id = "invalid"

    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, _to_write_dto(document))
    expected_msg = f"The import id {document.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.update.call_count == 0


def test_update_raises_when_invalid_variant(document_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document.variant_name = ""

    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, _to_write_dto(document))
    expected_msg = "Variant name is empty"
    assert e.value.message == expected_msg
    assert document_repo_mock.update.call_count == 0
