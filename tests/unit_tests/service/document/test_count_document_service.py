import pytest

import app.service.document as doc_service
from app.errors import RepositoryError
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


# --- COUNT


def test_count(document_repo_mock):
    result = doc_service.count()
    assert result is not None
    assert document_repo_mock.count.call_count == 1


def test_count_returns_none(document_repo_mock):
    document_repo_mock.return_empty = True
    result = doc_service.count()
    assert result is None
    assert document_repo_mock.count.call_count == 1


def test_count_raises_if_db_error(document_repo_mock):
    document_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        doc_service.count()

    expected_msg = "bad repo"
    assert e.value.message == expected_msg
    assert document_repo_mock.count.call_count == 1
