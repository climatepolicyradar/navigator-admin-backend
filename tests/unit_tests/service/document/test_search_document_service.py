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


# --- SEARCH


def test_search(document_repo_mock):
    result = doc_service.search({"q": "two"})
    assert result is not None
    assert len(result) == 1
    assert document_repo_mock.search.call_count == 1


def test_search_db_error(document_repo_mock):
    document_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        doc_service.search({"q": "error"})
    assert document_repo_mock.search.call_count == 1


def test_search_request_timeout(document_repo_mock):
    document_repo_mock.throw_timeout_error = True
    with pytest.raises(TimeoutError):
        doc_service.search({"q": "timeout"})
    assert document_repo_mock.search.call_count == 1


def test_search_missing(document_repo_mock):
    document_repo_mock.return_empty = True
    result = doc_service.search({"q": "empty"})
    assert result is not None
    assert len(result) == 0
    assert document_repo_mock.search.call_count == 1
